from odoo import models,api,fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    invoice_products_summary = fields.Text(
        string="Detalle",
        compute="_compute_invoice_products_summary",
        store=True
    )

    @api.depends('invoice_line_ids.product_id.name')
    def _compute_invoice_products_summary(self):
        for record in self:
            product_names = record.invoice_line_ids.mapped("product_id.name")
            record.invoice_products_summary = "\n".join(f"- {name}" for name in product_names)

