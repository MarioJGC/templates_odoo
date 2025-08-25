from odoo import models, _
from odoo.exceptions import ValidationError

class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_pe"
    
        
    # def _get_document_allowance_charge_vals_list(self, invoice):
    #     vals_list = super(AccountEdiXmlUBL20,
    #                       self)._get_document_allowance_charge_vals_list(invoice)
    #     special_lines = invoice.invoice_line_ids.filtered(
    #         lambda l: not l.display_type == 'line_section' and l.price_subtotal < 0 and
    #         (l.product_id.l10n_pe_advance or l.product_id.global_discount)
    #     )
    #     # Advance line
    #     for line in special_lines:
    #         if line.product_id.l10n_pe_advance:
    #             vals_list.append({
    #                 'charge_indicator': 'false',
    #                 'allowance_charge_reason_code': '02',
    #                 'allowance_charge_reason': _('Advance'),
    #                 'amount': line.price_total,
    #                 'currency_dp': 2,
    #                 'currency_name': invoice.currency_id.name,
    #             })
    #     if invoice.discount_lines_vals:
    #         for discount_line in invoice.discount_lines_vals:
    #             vals_list.append({
    #                 'charge_indicator': discount_line['discount_charge_indicator'],
    #                 'allowance_charge_reason_code': discount_line['discount_allowance_charge_reason_code'],
    #                 'allowance_charge_reason': discount_line['line'].name,
    #                 'amount': discount_line['discount_amount'],
    #                 'currency_dp': 2,
    #                 'currency_name': invoice.currency_id.name,
    #             })
    #     return vals_list
    
    def _export_invoice_vals(self, invoice):
        def grouping_key_generator(base_line, tax_values):
            tax = tax_values['tax_repartition_line'].tax_id
            tax_category_vals = self._get_tax_category_list(invoice, tax)[0]
            grouping_key = {
                'tax_category_id': tax_category_vals['id'],
                'tax_category_percent': tax_category_vals['percent'],
                '_tax_category_vals_': tax_category_vals,
                'tax_amount_type': tax.amount_type,
            }
            # If the tax is fixed, we want to have one group per tax
            # s.t. when the invoice is imported, we can try to guess the fixed taxes
            if tax.amount_type == 'fixed':
                grouping_key['tax_name'] = tax.name
            return grouping_key

        # Validate the structure of the taxes
        self._validate_taxes(invoice)

        # Compute the tax details for the whole invoice and each invoice line separately.
        taxes_vals = invoice._prepare_invoice_aggregated_taxes(
            grouping_key_generator=grouping_key_generator,
            filter_tax_values_to_apply=self._apply_invoice_tax_filter,
            filter_invl_to_apply=self._apply_invoice_line_filter,
        )

        # Fixed Taxes: filter them on the document level, and adapt the totals
        # Fixed taxes are not supposed to be taxes in real live. However, this is the way in Odoo to manage recupel
        # taxes in Belgium. Since only one tax is allowed, the fixed tax is removed from totals of lines but added
        # as an extra charge/allowance.
        fixed_taxes_keys = [k for k in taxes_vals['tax_details'] if k['tax_amount_type'] == 'fixed']
        for key in fixed_taxes_keys:
            fixed_tax_details = taxes_vals['tax_details'].pop(key)
            taxes_vals['tax_amount_currency'] -= fixed_tax_details['tax_amount_currency']
            taxes_vals['tax_amount'] -= fixed_tax_details['tax_amount']
            taxes_vals['base_amount_currency'] += fixed_tax_details['tax_amount_currency']
            taxes_vals['base_amount'] += fixed_tax_details['tax_amount']

        # Compute values for invoice lines.
        line_extension_amount = 0.0
        # NOTE: Inicio de modificación
        invoice_lines = invoice.invoice_line_ids.filtered(lambda line: line.display_type not in ('line_note', 'line_section'))
        # Solo se consideran las líneas con precio positivo en las facturas de venta
        if invoice.move_type == 'out_invoice':
            invoice_lines = invoice_lines.filtered(lambda line: line.price_subtotal > 0)
        # NOTE: Fin de modificación
        document_allowance_charge_vals_list = self._get_document_allowance_charge_vals_list(invoice)
        invoice_line_vals_list = []
        for line_id, line in enumerate(invoice_lines):
            line_taxes_vals = taxes_vals['tax_details_per_record'][line]
            line_vals = self._get_invoice_line_vals(line, line_id, line_taxes_vals)
            invoice_line_vals_list.append(line_vals)

            line_extension_amount += line_vals['line_extension_amount']

        # Compute the total allowance/charge amounts.
        allowance_total_amount = 0.0
        charge_total_amount = 0.0
        for allowance_charge_vals in document_allowance_charge_vals_list:
            if allowance_charge_vals['charge_indicator'] == 'false':
                allowance_total_amount += allowance_charge_vals['amount']
            else:
                charge_total_amount += allowance_charge_vals['amount']

        supplier = invoice.company_id.partner_id.commercial_partner_id
        customer = invoice.partner_id

        # OrderReference/SalesOrderID (sales_order_id) is optional
        sales_order_id = 'sale_line_ids' in invoice.invoice_line_ids._fields \
                         and ",".join(invoice.invoice_line_ids.sale_line_ids.order_id.mapped('name'))
        # OrderReference/ID (order_reference) is mandatory inside the OrderReference node !
        order_reference = invoice.ref or invoice.name

        vals = {
            'builder': self,
            'invoice': invoice,
            'supplier': supplier,
            'customer': customer,

            'taxes_vals': taxes_vals,

            'format_float': self.format_float,
            'AddressType_template': 'account_edi_ubl_cii.ubl_20_AddressType',
            'ContactType_template': 'account_edi_ubl_cii.ubl_20_ContactType',
            'PartyType_template': 'account_edi_ubl_cii.ubl_20_PartyType',
            'PaymentMeansType_template': 'account_edi_ubl_cii.ubl_20_PaymentMeansType',
            'PaymentTermsType_template': 'account_edi_ubl_cii.ubl_20_PaymentTermsType',
            'TaxCategoryType_template': 'account_edi_ubl_cii.ubl_20_TaxCategoryType',
            'TaxTotalType_template': 'account_edi_ubl_cii.ubl_20_TaxTotalType',
            'AllowanceChargeType_template': 'account_edi_ubl_cii.ubl_20_AllowanceChargeType',
            'SignatureType_template': 'account_edi_ubl_cii.ubl_20_SignatureType',
            'ResponseType_template': 'account_edi_ubl_cii.ubl_20_ResponseType',
            'DeliveryType_template': 'account_edi_ubl_cii.ubl_20_DeliveryType',
            'MonetaryTotalType_template': 'account_edi_ubl_cii.ubl_20_MonetaryTotalType',
            'InvoiceLineType_template': 'account_edi_ubl_cii.ubl_20_InvoiceLineType',
            'CreditNoteLineType_template': 'account_edi_ubl_cii.ubl_20_CreditNoteLineType',
            'DebitNoteLineType_template': 'account_edi_ubl_cii.ubl_20_DebitNoteLineType',
            'InvoiceType_template': 'account_edi_ubl_cii.ubl_20_InvoiceType',
            'CreditNoteType_template': 'account_edi_ubl_cii.ubl_20_CreditNoteType',
            'DebitNoteType_template': 'account_edi_ubl_cii.ubl_20_DebitNoteType',

            'vals': {
                'ubl_version_id': 2.1,
                'id': invoice.name,
                'issue_date': invoice.invoice_date,
                'due_date': invoice.invoice_date_due,
                'note_vals': self._get_note_vals_list(invoice),
                'order_reference': order_reference,
                'sales_order_id': sales_order_id,
                'accounting_supplier_party_vals': {
                    'party_vals': self._get_partner_party_vals(supplier, role='supplier'),
                },
                'accounting_customer_party_vals': {
                    'party_vals': self._get_partner_party_vals(customer, role='customer'),
                },
                'invoice_period_vals_list': self._get_invoice_period_vals_list(invoice),
                'delivery_vals_list': self._get_delivery_vals_list(invoice),
                'payment_means_vals_list': self._get_invoice_payment_means_vals_list(invoice),
                'payment_terms_vals': self._get_invoice_payment_terms_vals_list(invoice),
                # allowances at the document level, the allowances on invoices (eg. discount) are on line_vals
                'allowance_charge_vals': document_allowance_charge_vals_list,
                'tax_total_vals': self._get_invoice_tax_totals_vals_list(invoice, taxes_vals),
                'monetary_total_vals': self._get_invoice_monetary_total_vals(
                    invoice,
                    taxes_vals,
                    line_extension_amount,
                    allowance_total_amount,
                    charge_total_amount,
                ),
                'line_vals': invoice_line_vals_list,
                'currency_dp': self._get_currency_decimal_places(invoice.currency_id),  # currency decimal places
            },
        }

        # Document type specific settings
        if 'debit_origin_id' in self.env['account.move']._fields and invoice.debit_origin_id:
            vals['document_type'] = 'debit_note'
            vals['main_template'] = 'account_edi_ubl_cii.ubl_20_DebitNote'
            vals['vals']['document_type_code'] = 383
        elif invoice.move_type == 'out_refund':
            vals['document_type'] = 'credit_note'
            vals['main_template'] = 'account_edi_ubl_cii.ubl_20_CreditNote'
            vals['vals']['document_type_code'] = 381
        else: # invoice.move_type == 'out_invoice'
            vals['document_type'] = 'invoice'
            vals['main_template'] = 'account_edi_ubl_cii.ubl_20_Invoice'
            vals['vals']['document_type_code'] = 380

        # ========================
        # NOTE: Tomado del 2.1
        vals.update({
            'PaymentTermsType_template': 'account_edi_ubl_cii.ubl_21_PaymentTermsType',
            'CreditNoteLineType_template': 'account_edi_ubl_cii.ubl_21_CreditNoteLineType',
            'DebitNoteLineType_template': 'account_edi_ubl_cii.ubl_21_DebitNoteLineType',
            'InvoiceType_template': 'account_edi_ubl_cii.ubl_21_InvoiceType',
            'CreditNoteType_template': 'account_edi_ubl_cii.ubl_21_CreditNoteType',
            'DebitNoteType_template': 'account_edi_ubl_cii.ubl_21_DebitNoteType',
        })

        vals['vals'].update({
            'ubl_version_id': 2.1,
            'buyer_reference': invoice.commercial_partner_id.ref,
        })
        #----
        # NOTE: TOMADO DE l10n_pe_edi, como se sobreescribe el metodo aqui se elimina este codigo del modulo l10n_pe_edi
        supplier = invoice.company_id.partner_id.commercial_partner_id
        customer = invoice.commercial_partner_id

        vals['vals'].update({
            'customization_id': '2.0',
            'id': invoice.name.replace(' ', ''),
            'signature_vals': [{
                'id': 'IDSignKG',
                'signatory_party_vals': {
                    'party_id': invoice.company_id.vat,
                    'party_name': invoice.company_id.name.upper(),
                },
                'digital_signature_attachment_vals': {
                    'external_reference_uri': '#SignVX',
                },
            }],
        })

        vals['vals']['accounting_supplier_party_vals'].update({
            'customer_assigned_account_id': supplier.vat,
        })
        vals['vals']['accounting_supplier_party_vals']['party_vals']['party_legal_entity_vals'][0]['registration_address_vals'].update({
            'address_type_code': invoice.company_id.l10n_pe_edi_address_type_code,
        })

        vals['vals']['accounting_customer_party_vals'].update({
            'additional_account_id': (
                customer.l10n_latam_identification_type_id
                and customer.l10n_latam_identification_type_id.l10n_pe_vat_code
            ),
        })

        if vals['vals']['order_reference']:
            vals['vals']['order_reference'] = vals['vals']['order_reference'][:20]

        # Invoice specific changes
        if vals['document_type'] == 'invoice':
            vals['vals'].update({
                'document_type_code': invoice.l10n_latam_document_type_id.code,
                'document_type_code_attrs': {
                    'listID': invoice.l10n_pe_edi_operation_type,
                    'listAgencyName': 'PE:SUNAT',
                    'listName': 'Tipo de Documento',
                    'listURI': 'urn:pe:gob:sunat:cpe:see:gem:catalogos:catalogo01',
                },
            })
            if invoice.l10n_pe_edi_legend_value:
                vals['vals']['note_vals'].append({
                    'note': invoice.l10n_pe_edi_legend_value,
                    'note_attrs': {'languageLocaleID': invoice.l10n_pe_edi_legend},
                })
            vals['vals']['note_vals'].append({
                'note': invoice._l10n_pe_edi_amount_to_text(),
                'note_attrs': {'languageLocaleID': '1000'},
            })
            if invoice.l10n_pe_edi_operation_type == '1001':
                vals['vals']['note_vals'].append({
                    'note': 'Leyenda: Operacion sujeta a detraccion',
                    'note_attrs': {'languageLocaleID': '2006'},
                })

        # Credit Note specific changes
        if vals['document_type'] == 'credit_note':
            if invoice.l10n_latam_document_type_id.code == '07':
                vals['vals'].update({
                    'discrepancy_response_vals': [{
                        'response_code': invoice.l10n_pe_edi_refund_reason,
                        'description': invoice.ref
                    }]
                })
            if invoice.reversed_entry_id:
                vals['vals'].update({
                    'billing_reference_vals': {
                        'id': invoice.reversed_entry_id.name.replace(' ', ''),
                        'document_type_code': invoice.reversed_entry_id.l10n_latam_document_type_id.code,
                    },
                })

        # Debit Note specific changes
        if vals['document_type'] == 'debit_note':
            if invoice.l10n_latam_document_type_id.code == '08':
                vals['vals'].update({
                    'discrepancy_response_vals': [{
                        'response_code': invoice.l10n_pe_edi_charge_reason,
                        'description': invoice.ref
                    }]
                })
            if invoice.debit_origin_id:
                vals['vals'].update({
                    'billing_reference_vals': {
                        'id': invoice.debit_origin_id.name.replace(' ', ''),
                        'document_type_code': invoice.debit_origin_id.l10n_latam_document_type_id.code,
                    },
                })
        # ========================
        # NOTE: Inicio de modificación
        special_lines = invoice.invoice_line_ids.filtered(
            lambda l: not l.display_type == 'line_section' and l.price_subtotal < 0 and
            (l.product_id.l10n_pe_advance or l.product_id.global_discount)
        )
        advance_lines_vals = []
        discount_lines_vals = []
        i = 1
        total_advance = 0.00
        total_discount = 0.00

        discount_percent_global = invoice.discount_percent_global / 100
        for line in special_lines:
            # Advance line
            if line.product_id.l10n_pe_advance:
                if not line.l10n_pe_advance_invoice:
                    raise ValidationError(
                        f'{line.product_id.name}: Nombre de Anticipo vácio.')
                if invoice.l10n_latam_document_type_id.code == '01':
                    document_type_id_code = '02'
                elif invoice.l10n_latam_document_type_id.code == '03':
                    document_type_id_code = '03'
                else:
                    document_type_id_code = invoice.l10n_latam_document_type_id.code or ''
                advance_line = {
                    'index': i,
                    'line': line,
                    'advance_name': line.l10n_pe_advance_invoice,
                    'partner_vat': invoice.partner_id.vat,
                    'company_vat': invoice.company_id.vat,
                    'company_type_document': invoice.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
                    'l10n_latam_document_type_id': document_type_id_code,
                    'datetime_document': invoice.invoice_date,
                    'tax_inclusive_amount': abs(line.price_total)
                }
                total_advance += advance_line['tax_inclusive_amount']
                advance_lines_vals.append(advance_line)
                i += 1

            # Discount global line
            if line.product_id.global_discount:
                product_id = line.product_id
                reason_code = product_id.l10n_pe_charge_discount or '00'
                discount_global_line = {
                    'line': line,
                    'discount_charge_indicator': 'false' if reason_code not in ['45', '46', '47'] else 'true',
                    'discount_allowance_charge_reason_code': reason_code,
                    'discount_percent': discount_percent_global,
                    'discount_amount': abs(line.price_subtotal),
                    'base_amount': abs(line.price_subtotal / discount_percent_global),
                }
                if reason_code == '03':
                    total_discount += abs(line.price_subtotal)

                discount_lines_vals.append(discount_global_line)

        # if advance_lines_vals:
        vals['advance_lines_vals'] = advance_lines_vals
        vals['total_advance'] = total_advance

        # if discount_lines_vals:
        vals['discount_lines_vals'] = discount_lines_vals
        vals['total_discount'] = total_discount
        vals.update({
            'payable_amount': vals['vals']['monetary_total_vals']['payable_amount'] - total_advance
        })
        # NOTE: Fin de modificación
        return vals
    
    
    def _get_invoice_monetary_total_vals(self, invoice, taxes_vals, line_extension_amount, allowance_total_amount, charge_total_amount):
        # EXTENDS account.edi.xml.ubl_21
        vals = super()._get_invoice_monetary_total_vals(invoice, taxes_vals, line_extension_amount, allowance_total_amount, charge_total_amount)
        special_lines = invoice.invoice_line_ids.filtered(
            lambda l: not l.display_type == 'line_section' and l.price_subtotal < 0 and
            (l.product_id.l10n_pe_advance)
        )
        if special_lines:
            total_advance = sum(line.price_total for line in special_lines if line.product_id.l10n_pe_advance)
            vals['prepaid_amount'] = abs(total_advance)
        return vals