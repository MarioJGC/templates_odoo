from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.onchange('l10n_pe_advance')
    def checkbox_set_true_advance(self):
        for product in self:
            if product.l10n_pe_advance:
                product.global_discount = True
                product.l10n_pe_charge_discount = '04'
