from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_placa = fields.Char(string='Placa')

    car_plate_ids = fields.One2many('car.plate', 'partner_id', string="Placas de Auto")
