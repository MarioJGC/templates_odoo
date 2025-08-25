from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    discount_percent_global = fields.Float(
        string='Descuento Global (%)',
        compute='_compute_amount',
        store=True
    )

    @api.onchange('invoice_line_ids')
    def _onchange_quick_edit_line_ids(self):
        super(AccountMove, self)._onchange_quick_edit_line_ids()
        self._compute_discount_percent_global()
        self._compute_amount_temporal()

    def _compute_amount_temporal(self):
        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            for line in move.line_ids:
                if move.is_invoice(True) and line.display_type in ('product', 'rounding'):
                    total_untaxed += line.balance
                    total_untaxed_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move_amount_untaxed = (
                sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed))
            move.write_percent_global(move_amount_untaxed)

    @api.depends(
        'line_ids.matched_debit_ids.debit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_debit_ids.debit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.matched_credit_ids.credit_move_id.move_id.payment_id.is_matched',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual',
        'line_ids.matched_credit_ids.credit_move_id.move_id.line_ids.amount_residual_currency',
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'line_ids.payment_id.state',
        'line_ids.full_reconcile_id')
    def _compute_amount(self):
        for move in self:

            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_to_pay = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = move._get_lines_onchange_currency().currency_id

            for line in move.line_ids:
                if move.is_invoice(True):
                    # === Invoices ===
                    if line.display_type == 'tax' or (line.display_type == 'rounding' and line.tax_repartition_line_id):
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type in ('product', 'rounding'):
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.display_type == 'payment_term':
                        # Residual amount.
                        total_to_pay += line.balance
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.move_type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = (
                sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed))
            move.amount_tax = (
                sign * (total_tax_currency if len(currencies) == 1 else total_tax))
            move.amount_total = (
                sign * (total_currency if len(currencies) == 1 else total))
            move.amount_residual = (
                -sign * (total_residual_currency if len(currencies) == 1 else total_residual))
            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = (
                abs(total) if move.move_type == 'entry' else -total)
            move.amount_residual_signed = total_residual
            move.amount_total_in_currency_signed = (
                abs(move.amount_total) if move.move_type == 'entry' else -(sign * move.amount_total))

            currency = currencies if len(
                currencies) == 1 else move.company_id.currency_id

            # Compute 'payment_state'.
            new_pmt_state = 'not_paid' if move.move_type != 'entry' else False

            if move.is_invoice(include_receipts=True) and move.state == 'posted':
                if currency.is_zero(move.amount_residual):
                    reconciled_payments = move._get_reconciled_payments()
                    if not reconciled_payments or all(payment.is_matched for payment in reconciled_payments):
                        new_pmt_state = 'paid'
                    else:
                        new_pmt_state = move._get_invoice_in_payment_state()
                elif currency.compare_amounts(total_to_pay, total_residual) != 0:
                    new_pmt_state = 'partial'

            if new_pmt_state == 'paid' and move.move_type in ('in_invoice', 'out_invoice', 'entry'):
                reverse_type = move.move_type == 'in_invoice' and 'in_refund' or move.move_type == 'out_invoice' and 'out_refund' or 'entry'
                reverse_moves = self.env['account.move'].search(
                    [('reversed_entry_id', '=', move.id), ('state', '=', 'posted'), ('move_type', '=', reverse_type)])
                caba_moves = self.env['account.move'].search(
                    [('tax_cash_basis_origin_move_id', 'in', move.ids + reverse_moves.ids), ('state', '=', 'posted')])

                # We only set 'reversed' state in cas of 1 to 1 full reconciliation with a reverse entry; otherwise, we use the regular 'paid' state
                # We ignore potentials cash basis moves reconciled because the transition account of the tax is reconcilable
                reverse_moves_full_recs = reverse_moves.mapped(
                    'line_ids.full_reconcile_id')
                if reverse_moves_full_recs.mapped('reconciled_line_ids.move_id').filtered(lambda x: x not in (
                        caba_moves + reverse_moves + reverse_moves_full_recs.mapped('exchange_move_id'))) == move:
                    new_pmt_state = 'reversed'

            move.payment_state = new_pmt_state

        self._compute_discount_percent_global()

        for record in self:
            if record.discount_percent_global == 100:
                move.amount_untaxed = 0.00
                move.amount_tax = 0.00
                move.amount_total = 0.00
                move.amount_residual = 0.00
                move.amount_untaxed_signed = 0.00
                move.amount_tax_signed = 0.00
                move.amount_total_signed = 0.00
                move.amount_residual_signed = 0.00
                move.amount_total_in_currency_signed = 0.00

    def _compute_discount_percent_global(self):
        for move in self:

            if move.payment_state == 'invoicing_legacy':
                # invoicing_legacy state is set via SQL when setting setting field
                # invoicing_switch_threshold (defined in account_accountant).
                # The only way of going out of this state is through this setting,
                # so we don't recompute it here.
                move.payment_state = move.payment_state
                continue

            move.write_percent_global(move.amount_untaxed)

            # if subtotal advance != 0
            number_invoice_lines = 0
            for line in move.invoice_line_ids:
                number_invoice_lines += 1
                if number_invoice_lines == 1 and line.product_id.global_discount:
                    move.discount_percent_global = 0.00

    def write_percent_global(self, move_amount_untaxed):
        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)

                if move.is_invoice(include_receipts=True):
                    # === Invoices ===
                    if line.product_id.global_discount:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency

            discount_percent_global = abs(total_untaxed_currency if len(
                currencies) == 1 else abs(total_untaxed))
            value = move_amount_untaxed + discount_percent_global
            move.discount_percent_global = (
                discount_percent_global / value) * 100 if value != 0 else 0

            if move.state == 'posted':
                move.write({'discount_percent_global': (
                    discount_percent_global / value) * 100 if value != 0 else 0})
