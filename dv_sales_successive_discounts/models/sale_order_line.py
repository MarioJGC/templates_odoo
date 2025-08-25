from re import T
from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    product_id_aux = fields.Many2one(
        comodel_name='product.product',
        string="Product Aux",
        change_default=True)

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:

            if line.price_unit == 0 or line.product_template_id.list_price == line.price_unit:

                if line.qty_invoiced > 0 or (line.product_id.expense_policy == 'cost' and line.is_expense):
                    continue
                if not line.product_uom or not line.product_id:
                    line.price_unit = 0.0
                else:
                    line = line.with_company(line.company_id)
                    price = line._get_display_price()
                    line.price_unit = line.product_id._get_tax_included_unit_price_from_price(
                        price,
                        line.currency_id or line.order_id.currency_id,
                        product_taxes=line.product_id.taxes_id.filtered(
                            lambda tax: tax.company_id == line.env.company
                        ),
                        fiscal_position=line.order_id.fiscal_position_id,
                    )


    def open_wizard_successive_discounts(self):
        self.ensure_one() 

        discount = self.env['sale.successive.discounts'].search([
            ('sale_order_line_id', '=', self.id)
        ], limit=1)

        if not discount:

            discount = self.env['sale.successive.discounts'].create({
                'sale_order_line_id': self.id,
                'original_price': self.price_unit,
                'seller_id': self.order_id.user_id.partner_id.id
            })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Descuentos Sucesivos',
            'res_model': 'sale.successive.discounts',
            'res_id': discount.id,
            'view_mode': 'form',
            'target': 'new',
        }
