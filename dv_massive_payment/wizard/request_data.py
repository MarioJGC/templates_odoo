from odoo import models, api, fields
from odoo.exceptions import UserError

class RequestData(models.TransientModel):

    _name = 'request.data'

    account_move_lines = fields.Many2many(
        'account.move', 'account_payment_register_request', 'account_payment_register_id', 'account_move_id',
        string='Facturas a pagar', store=True
    )

    # Campos requeridos
    payment_date_req = fields.Date(string='Fecha de Pago')

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        help="Moneda a realizar el pago")

    
    @api.model
    def create(self, vals):
        res = super(RequestData, self).create(vals)

        # Validación de facturas
        partner_id = res.account_move_lines[0].partner_id
        for i in res.account_move_lines:
            if i.amount_residual <= 0:
                raise UserError(f"El monto de la factura {i.amount_residual} es menor o igual a 0.")
            if i.partner_id != partner_id:
                raise UserError(f"El cliente debe ser el mismo en todas las facturas.")

        return res

    def set_date_currency_and_register_payment(self):

        var = self.env['massive.payment.register'].create({
            'payment_date': self.payment_date_req,
            'list_invoices_ids': self.account_move_lines,
            'currency_id': self.currency_id.id
        })
        
        return {
            'name': 'Registrar pago de Facturas',
            'type': 'ir.actions.act_window',
            'res_model': 'massive.payment.register',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': var.id,
            'target': 'new',
        }

    