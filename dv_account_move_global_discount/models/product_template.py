from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    global_discount = fields.Boolean(string='Usado como Descuento global')