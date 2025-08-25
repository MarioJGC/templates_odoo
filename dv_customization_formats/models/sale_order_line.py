from io import StringIO
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    discount_custom = fields.Float(string="Descuento", store=True, readonly=False)

    count = fields.Float(string='Valor inicial', store=True,readonly=False)

    def _prepare_invoice_line(self, **kwargs):
        res = super()._prepare_invoice_line(**kwargs)
        res.update({'discount_custom': self.discount_custom})
        return res

    @api.onchange('discount_custom','product_uom_qty','price_unit')
    def _compute_discount_custom(self):
        for line in self:

            value_init = 0
            value_final = 0

            if line.discount_custom != 0 and line.discount_custom > 0:

                # Precio por cantidad

                value_init = line.price_unit * line.product_uom_qty
                value_final = value_init - line.discount_custom

                # Caluclate discount %
                line.discount = ((value_init - value_final) / value_init) * 100
            
            else:
                line.discount = 0
                line.discount_custom = 0