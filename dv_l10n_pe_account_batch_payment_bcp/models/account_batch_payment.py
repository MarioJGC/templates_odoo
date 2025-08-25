from odoo import api, fields, models
import base64


class AccountBatchPayment(models.Model):
    _inherit = 'account.batch.payment'

    tlcdt_exonerate_itf = fields.Boolean(string="Exonerar ITF", default=False)
    tlcdt_validate_idc = fields.Boolean(string="Validar IDC", default=False,
                                        help="Si desea que se valide que el Documento de Identidad del Beneficiario (IDC) que indica en la planilla sea igual al que tenemos registrado en el banco, colocar la letra 'S'. De lo contrario colocar la letra 'N'")

    def format_amount(self, amount, length):
        """
            Formatea el monto a 17 caracteres con 2 decimales
        """
        amount_str = str(round(amount, 2))
        if len(amount_str.split('.')[1]) < 2:
            formatted_amount = amount_str + '0'
        else:
            formatted_amount = str(round(amount, 2))

        result = formatted_amount.rjust(length, '0')
        return result

    def _get_telecredito_genericity_warnings(self):
        telecredito_warnings = []
        no_partner_bank_acc_payments = self.env['account.payment']
        different_currency_payments = self.env['account.payment']
        no_partner_vat_payments = self.env['account.payment']

        if not self.journal_id.bank_account_id:
            telecredito_warnings.append({
                'code': 'no_journal_bank_account',
                'title': f"El diario {self.journal_id.name} no tiene cuenta bancaria asociada. Por favor, asocie una cuenta bancaria a este diario.",
                'records': self.journal_id,
            })

        for payment in self.mapped('payment_ids'):
            payment_currency = payment.currency_id.name
            if self.journal_id.currency_id and payment_currency != self.journal_id.currency_id:
                different_currency_payments += payment
            if not payment.partner_id.get_telecredito_partner_priority_bank_id():
                no_partner_bank_acc_payments += payment
            if not payment.partner_id.vat:
                no_partner_vat_payments += payment

        if different_currency_payments:
            different_currency_payments_names = ', '.join(
                different_currency_payments.mapped('name'))
            telecredito_warnings.append({
                'code': 'currency_mismatch',
                'title': f"Los siguientes pagos tienen una moneda diferente al del diario {self.journal_id.name}: {different_currency_payments_names}. Telecrédito solo acepta pagos en la misma moneda de la cuenta de cargo.",
                'records': different_currency_payments,
            })
        if no_partner_bank_acc_payments:
            no_partner_bank_acc_payments_names = ', '.join(
                no_partner_bank_acc_payments.mapped('partner_id.name'))
            telecredito_warnings.append({
                'code': 'no_partner_bank_acc',
                'title': f"Los siguientes contactos no tienen una cuenta bancaria válida: {no_partner_bank_acc_payments_names}. Debe tener una cuenta del banco BCP o una cuenta de otro banco configurada como cuenta interbancaria.",
                'records': no_partner_bank_acc_payments,
            })
        if no_partner_vat_payments:
            no_partner_vat_payments_names = ', '.join(
                no_partner_vat_payments.mapped('partner_id.name'))
            telecredito_warnings.append({
                'code': 'no_partner_vat',
                'title': f"Los siguientes contactos no tienen registrado su VAT: {no_partner_vat_payments_names}",
                'records': no_partner_vat_payments,
            })
        return telecredito_warnings

    def check_payments_for_warnings(self):
        res = super(AccountBatchPayment, self).check_payments_for_warnings()
        if self.payment_method_code == 'telecredito':
            telecredito_warnings = self._get_telecredito_genericity_warnings()
            res += telecredito_warnings
        return res

    def button_draft(self):
        self.ensure_one()
        if self.payment_ids:
            self.payment_ids.unmark_as_sent()
        self.write({
            'export_file': False,
            'export_filename': False
        })

    def _get_documents_grouped_by_partner_vat(self):
        """
            Devuelve una lista de recordset de la forma
            list_grouped = [account.payment(1, 2, 5, ), account.payment(3, ), account.payment(4, 6, )]
            Donde cada recordset contiene pagos de un mismo partner_id.vat
        """
        self.ensure_one()
        self.ensure_one()
        unique_payment_groups = set()

        for payment in self.payment_ids:
            payment_group = self.payment_ids.filtered(
                lambda x: x.partner_id.vat == payment.partner_id.vat)
            unique_payment_groups.add(payment_group)

        documents_grouped_by_vat = list(unique_payment_groups)
        return documents_grouped_by_vat

    def _generate_telecredito_file(self):
        HEADER_TEMPLATE = '{id}{lines_total}{date}{c}{currency}{acc_number}{amount_total}{reference}{N}{abono}\r\n'
        PARTNER_TEMPLATE = '{id}{bank_cod}{account}{id_2}{doc}{vat}{spaces}{ref}{reference}{reference_2}{currency}{amount}{N}\r\n'
        DOCUMENT_RAW = '{id}{document}{ref}{amount}\r\n'
        content_raw = ''
        amount_total = 0
        documents_count = len(self.payment_ids)
        partners_count = len(self.payment_ids.partner_id.mapped('vat'))
        journal_acc_number = self.journal_id.bank_account_id.acc_number
        sum_account_numbers = 0
        # Esta retornando mas de una cuenta
        sum_account_numbers += self.journal_id.bank_account_id.get_telecredito_account_number_integer()
        documents_grouped_by_vat = self._get_documents_grouped_by_partner_vat()
        for group in documents_grouped_by_vat:
            partner_id = group.mapped('partner_id')[0]
            # Esta retornando vacio
            partner_bank_id = partner_id.get_telecredito_partner_priority_bank_id()
            sum_account_numbers += partner_bank_id.get_telecredito_account_number_integer()
            first_payment = group[0]  # TODO que pasa si hay pagos multimoneda?
            content_raw += PARTNER_TEMPLATE.format(
                id='2',
                bank_cod=partner_bank_id.get_telecredito_bank_type_code(),
                account=partner_bank_id.get_telecredito_account_number(),
                id_2='1',  # Modalidad de pago 1: Efectivo , 2: Cheque
                doc=partner_id.get_telecredito_identification_code(),
                vat=partner_id.vat.ljust(12, ' '),
                spaces='   ',
                ref=partner_id.name[:75].ljust(75, ' '),
                reference=f"Referencia Beneficiario {partner_id.vat}".ljust(
                    40, ' '),
                reference_2=f"Ref Emp {partner_id.vat}".ljust(20, ' '),
                currency='0001' if first_payment.currency_id.name == 'PEN' or not first_payment.currency_id else '1001',
                amount=self.format_amount(sum(group.mapped('amount')), 17),
                N='S' if self.tlcdt_validate_idc else 'N',
            )

            for payment in group:
                amount_total += payment.amount
                content_raw += DOCUMENT_RAW.format(
                    id='3',
                    document=payment.get_bill_document_type_code(),
                    ref=payment.get_telecredito_payment_ref(),
                    amount=self.format_amount(payment.amount, 17),
                )

        header_raw = HEADER_TEMPLATE.format(
            id='1',
            lines_total=str(partners_count).rjust(6, '0'),
            date=self.date.strftime("%Y%m%d"),
            c='C',
            currency='0001' if self.journal_id.currency_id.name == 'PEN' or not self.journal_id.currency_id else '1001',
            acc_number=journal_acc_number.ljust(20, ' '),
            amount_total=self.format_amount(amount_total, 17),
            reference=self.name.ljust(40, ' '),
            N='S' if self.tlcdt_exonerate_itf else 'N',
            abono=str(sum_account_numbers)[-15:].rjust(15, '0'),
        )
        raw_txt = header_raw + content_raw
        return raw_txt

    def _get_methods_generating_files(self):
        res = super(AccountBatchPayment, self)._get_methods_generating_files()
        res.append('telecredito')
        return res

    def _generate_export_file(self):
        if self.payment_method_code == "telecredito":
            data = self._generate_telecredito_file()
            return {
                "file": base64.encodebytes(data.encode()),
                "filename": "TLCDT-%s-%s.txt" % (self.journal_id.code, self.date.strftime("%d-%m-%Y")),
            }
        else:
            return super(AccountBatchPayment, self)._generate_export_file()
