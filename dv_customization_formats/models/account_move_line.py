from odoo import models, api, fields

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    discount_custom = fields.Float(string="Descuento")

    @api.onchange('discount_custom','quantity','price_unit')
    def _compute_discount_custom(self):
        for line in self:

            value_init = 0
            value_final = 0

            if line.discount_custom != 0 and line.discount_custom > 0:

                value_init = line.quantity * line.price_unit
                value_final = value_init - line.discount_custom

                # Caluclate discount %
                line.discount = ((value_init - value_final) / value_init) * 100
            
            else:
                line.discount = 0
                line.discount_custom = 0