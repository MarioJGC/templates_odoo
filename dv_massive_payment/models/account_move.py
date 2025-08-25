from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import date

class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_to_payment = fields.Float(
        string='Monto a pagar',
        store=True,
    )

    @api.depends('amount_total')
    def _compute_amount_to_payment(self):
        for record in self:
            record.amount_to_payment = record.amount_total

    def register_payment(self):
        selected_invoices = self.env['account.move'].browse(self.env.context.get('active_ids', []))

        var = self.env['request.data'].create({
            'account_move_lines': selected_invoices.ids
        })
        
        return {
            'name': 'Registrar Pago',
            'type': 'ir.actions.act_window',
            'res_model': 'request.data',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': var.id,
            'target': 'new',
        }