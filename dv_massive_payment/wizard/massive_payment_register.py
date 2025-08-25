from math import e
from odoo import models, api, fields
from odoo.exceptions import UserError
from datetime import datetime

class MassivePaymentRegister(models.TransientModel):
    _name= 'massive.payment.register'

    list_invoices_ids = fields.Many2many(
        'account.move', 'account_payment_register_massive', 'account_payment_register_id', 'account_move_id',
        string='Facturas a pagar', store=True
    )

    amount = fields.Monetary(string='Monto', compute='_compute_update_incoices_and_amount_total')

    amount_aux = fields.Monetary(string='Monto auxiliar', compute='_compute_calculate_amount_payment')

    payment_date = fields.Date(string="Payment Date", required=True,
        default=fields.Date.context_today, store=True)

    communication = fields.Char(string='Memo', store=True)

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')

    payment_difference = fields.Monetary(
        string='Diferencia de pago',
        compute='_compute_payment_difference',
        currency_field='currency_id', store=True)

    payment_difference_handling = fields.Selection(
        string="Manejo de diferencia de pagos",
        selection=[('open', 'Mantener abierto'), ('reconcile', 'Marcar como pagado en su totalidad')],
        default='open',
        store=True,
        readonly=False,)

    writeoff_account_id = fields.Many2one(
        comodel_name='account.account',
        string="Publicar diferencia en",
        copy=False)

    writeoff_label = fields.Char(string='Etiqueta', default='Diferencia de cambio')

    payment_type = fields.Selection(
        selection=[
            ('outbound', 'Enviar'),
            ('inbound', 'Recibir'),
        ],
        string='Tipo de Pago', store=True)

    payment_method_line_id = fields.Many2one(
        'account.payment.method.line', 
        string='Método de Pago',
        domain="[('id', 'in', payment_method_line_ids)]",)

    payment_method_line_ids = fields.Many2many(
        'account.payment.method.line', )

    journal_id = fields.Many2one(
        'account.journal', 
        string='Diario', store=True,
        domain="[('type', 'in', ('bank', 'cash'))]")

    state_group = fields.Boolean()

    group_payment = fields.Boolean(string='Agrupar pagos',
        default=True,
        store=True)

    @api.model
    def create(self, vals):
        res = super(MassivePaymentRegister, self).create(vals)

        journal = self.env['account.journal'].search([
            ('type', 'in', ('bank', 'cash')),
            ('company_id', '=', self.env.company.id),
            ('currency_id','=',res.currency_id.id)
        ], limit=1)

        if journal:
            res.journal_id = journal.id

        invoice = res.list_invoices_ids[0]
        res.payment_type = 'inbound' if invoice.move_type == 'out_invoice' else 'outbound'
        res.payment_method_line_ids = res.journal_id.inbound_payment_method_line_ids if res.payment_type == 'inbound' else res.journal_id.outbound_payment_method_line_ids
        res.payment_method_line_id =res.env['account.payment.method.line'].search([
            ('id', 'in', res.payment_method_line_ids.ids),
            ('company_id', '=', res.env.company.id)
        ], limit=1) or False

        res.state_group = True if len(res.list_invoices_ids) > 1 else False

        # Validaciones
        partner_id = res.list_invoices_ids[0].partner_id
        for i in res.list_invoices_ids:
            if i.amount_residual <= 0:
                raise UserError(f"El monto de la factura {i.amount_residual} es menor o igual a 0.")
            if i.partner_id != partner_id:
                raise UserError(f"El cliente debe ser el mismo en todas las facturas.")

        return res

    # ONCHANGE METHODS
    @api.onchange('list_invoices_ids')
    def _onchange_trigger_method(self):
        self._compute_calculate_amount_payment()
    
    # DEPENDS METHODS
    @api.depends('list_invoices_ids.amount_to_payment')
    def _compute_calculate_amount_payment(self):
        sum_amount = 0
        for invoice in self.list_invoices_ids:
            sum_amount += invoice.amount_to_payment
        self.amount_aux = sum_amount

        if self.amount_aux != self.amount:
            self.amount = self.amount_aux

        if len(self.list_invoices_ids) > 1:
            self.state_group = True
        else:
            self.state_group = False

        reconcile_domain = [
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
        ]

        memo_list = []
        for invoice in self.list_invoices_ids:
            lines_in_invoice = invoice.line_ids.filtered_domain(reconcile_domain)

            if len(lines_in_invoice) > 1:
                invoice_name = " ".join(invoice.name.split()) 
                formatted_name = f"{invoice_name} cuota #1"
                memo_list.append(formatted_name)

            else:
                memo_list.append(invoice.name)

        self.communication = ' '.join(memo_list)

    @api.depends('amount')
    def _compute_payment_difference(self):
        amount = self.amount
        if amount != self.amount_aux:
            self.payment_difference = self.amount_aux - amount
            self.amount = amount
        else:
            self.payment_difference = 0.0

    @api.depends('payment_date','currency_id')
    def _compute_update_incoices_and_amount_total(self):
        reconcile_domain = [
            ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
        ]

        memo_list = []
        for invoice in self.list_invoices_ids:
            lines_in_invoice = invoice.line_ids.filtered_domain(reconcile_domain)

            if len(lines_in_invoice) > 1:
                invoice_name = " ".join(invoice.name.split()) 
                formatted_name = f"{invoice_name} cuota #1"
                memo_list.append(formatted_name)

            else:
                memo_list.append(invoice.name)

        self.communication = ' '.join(memo_list)

        self.amount = self.calculate_total_in_currency(
            self.currency_id.name,
            self.list_invoices_ids,
            self.payment_date)

    # BUSINESS METHODS
    def calculate_total_in_currency(self, currency_code, invoices, date_wizardd):
        target_currency = self.env['res.currency'].search([('name', '=', currency_code)], limit=1)
        if not target_currency:
            raise UserError(f"La moneda '{currency_code}' no existe en el sistema.")

        total = 0.0
        date = date_wizardd

        for invoice in invoices:
            invoice_currency = invoice.currency_id

            converted_amount = invoice_currency._convert(
                invoice.amount_residual,
                target_currency,
                invoice.company_id,
                date
            )
            invoice.amount_to_payment = converted_amount
            total += converted_amount

        return total

    def ensure_amount_in_soles(self, amount, company, date_conversion):
        """
        Verifica si el monto está en Soles (PEN). Si no lo está, lo convierte.
        
        Parámetros:
            - amount: Monto a validar/convertir.
            - company: Compañía para la conversión.
            - date_conversion: Fecha a usar para la conversión.
        
        Retorna:
            - Monto en Soles (PEN).
        """
        self.ensure_one()

        # Buscar la moneda en Soles (PEN)
        pen_currency = self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
        if not pen_currency:
            raise UserError("La moneda 'PEN' no está configurada en el sistema.")

        # Si el wizard ya está en Soles, dejar el monto tal como está
        if self.currency_id == pen_currency:
            return round(amount, self.currency_id.decimal_places)

        # Convertir a Soles (PEN) si la moneda del wizard es diferente
        converted_amount = self.currency_id._convert(
            amount,            # Monto a convertir
            pen_currency,      # Moneda destino (Soles)
            company,           # Compañía
            date_conversion    # Fecha de conversión
        )

        return converted_amount

        
    def execute_register_payment(self):

        partner = None
        precision = self.currency_id.decimal_places
        partner = self.list_invoices_ids[0].partner_id

        reconcile_domain = [('account_id.account_type', 'in', ['asset_receivable', 'liability_payable'])]
        reconcile_domain_account = [('account_id.account_type', 'not in', ['asset_receivable', 'liability_payable'])]
        
        # Si es un pago agrupado o la longitud de facturas es solo 1 (Esto si tiene diferencia de cambio)
        if self.group_payment is True:

            total_amount = 0
            invoice_lines = []

            for invoice in self.list_invoices_ids:
                if invoice.amount_to_payment <= 0:
                    raise ValueError("El monto a pagar debe ser mayor a cero")
                if partner and partner != invoice.partner_id:
                    raise ValueError("Las facturas deben pertenecer al mismo cliente.")

                total_amount += invoice.amount_to_payment

                invoice_lines.append((invoice, self.ensure_amount_in_soles(invoice.amount_to_payment,invoice.company_id,self.payment_date)))
            
            total_amount = round(total_amount, precision)

            # Crear el pago
            payment = self.env['account.payment'].create({
                'ref': self.communication,
                'partner_id': partner.id,
                'amount': total_amount,
                'currency_id': self.currency_id.id,
                'date': self.payment_date,
                'payment_method_line_id': self.payment_method_line_id.id,
                'journal_id': self.journal_id.id,
                'payment_type': self.payment_type,
                'partner_type': 'customer',
            })

            payment = payment.with_context(skip_account_move_synchronization=True)

            # Extraer las cuenta por pagar del movimiento de pago
            origin_payment_line = payment.move_id.line_ids.filtered_domain(reconcile_domain)
            account_debit_line = payment.move_id.line_ids.filtered_domain(reconcile_domain_account)
            
            # Generar los apuntes contables correspondientes
            account_move_lines = []

            # Crear los apuntes contables por factura
            sum_credit = 0
            for invoice in self.list_invoices_ids:
                invoice_amount = round(invoice.amount_to_payment, precision)
                value_credit = self.ensure_amount_in_soles(invoice.amount_to_payment,invoice.company_id,self.payment_date)
            
                account_move_lines.append({
                    'account_id': origin_payment_line.account_id.id,
                    'partner_id': invoice.partner_id.id,
                    'name': invoice.name,
                    'credit': value_credit,
                    'debit': 0,
                    'amount_currency': -invoice_amount, # Va a credito
                    'currency_id': self.currency_id.id,
                    'date_maturity': origin_payment_line.date_maturity,
                })

                sum_credit += value_credit

            # Validación si tiene diferencia de cambio
            value_difference_total = 0
            amount_diference_credit = 0
            if self.payment_difference != 0:
                value_difference_total = abs(self.payment_difference) if self.payment_difference < 0 else -(self.payment_difference)
                value_difference_total = round(value_difference_total, precision)
                value_difference = round(self.payment_difference, precision)

                debit_or_credit = value_difference
                if self.currency_id.name != 'PEN':
                    # Dolares
                    pen_currency = self.env['res.currency'].search([('name', '=', 'PEN')], limit=1)
                    if not pen_currency:
                        raise UserError("La moneda 'PEN' no está configurada en el sistema.")

                    converted_amount = self.currency_id._convert(
                        debit_or_credit,  # Monto pendiente de pago
                        pen_currency, # Moneda destino (Soles)
                        self.list_invoices_ids[0].company_id, # Compañía
                        self.payment_date  # Fecha de conversión
                        )

                    converted_amount_credit = self.currency_id._convert(
                        value_difference_total,  # Monto pendiente de pago
                        pen_currency, # Moneda destino (Soles)
                        self.list_invoices_ids[0].company_id, # Compañía
                        self.payment_date  # Fecha de conversión
                        )
                    
                    debit_or_credit = converted_amount
                    amount_diference_credit = converted_amount_credit

                account_move_lines.append({
                    'account_id': self.writeoff_account_id.id,
                    'partner_id': partner.id,
                    'name': self.writeoff_label,
                    'credit':abs(debit_or_credit) if value_difference < 0 else 0,
                    'debit':abs(debit_or_credit) if value_difference > 0 else 0,
                    'amount_currency': value_difference, # Puede ser credito o debito
                    'currency_id': self.currency_id.id,
                    'tax_ids': [(6, 0, origin_payment_line.tax_ids.ids)],
                    'date_maturity': origin_payment_line.date_maturity,
                })
            
            # Crear el apunte contable del monto total
            total_debit = total_amount + value_difference_total
            total_debit = round(total_debit, precision)
            account_move_lines.append({
                'account_id': account_debit_line.account_id.id,
                'partner_id': partner.id,
                'name': origin_payment_line.name,
                'credit': 0,
                'debit': sum_credit + amount_diference_credit,
                'amount_currency': total_debit, # Va a debito
                'currency_id': self.currency_id.id,
                'tax_ids': [(6, 0, origin_payment_line.tax_ids.ids)],
                'date_maturity': origin_payment_line.date_maturity,
            })

            payment.move_id.line_ids.sudo().unlink()
            payment.move_id.write({'line_ids': [(0, 0, line) for line in account_move_lines]})
            payment.move_id.action_post()

            # Conciliación
            for invoice, amount in invoice_lines:
                
                reconcile_domain = [('account_id.reconcile', '=', True),
                                ('account_id.account_type', 'in', ['asset_receivable', 'liability_payable']),
                                ('name','=',invoice.name)]

                # Obtenemos el apunte contable del pago creado
                lines_to_reconcile = payment.move_id.line_ids.filtered_domain(reconcile_domain)
                
                # Filtramos los apuntes contables con la misma cuenta de la factura y que todavia no han sido conciliados
                invoice_line_to_reconcile = invoice.line_ids.filtered(lambda l: l.account_id == lines_to_reconcile.account_id and l.reconciled == False)

                for line in invoice_line_to_reconcile[0]:
                    
                    if amount <= 0:
                        break
                    
                    if line.amount_residual >= amount:
                        (lines_to_reconcile + line).reconcile()
                        amount = 0

                    else:
                        amount -= line.amount_residual
                        (lines_to_reconcile + line).reconcile()

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'res_id': payment.id,
                'view_mode': 'form',
                'target': 'current',
            }