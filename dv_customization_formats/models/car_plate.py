from odoo import models, fields

class CarPlate(models.Model):
    _name = 'car.plate'
    _description = 'Placa de Auto'

    plate_number = fields.Char(string='Número de Placa', required=True)
    partner_id = fields.Many2one('res.partner', string='Contacto', ondelete='cascade')

    _sql_constraints = [
        ('unique_plate_number', 'unique(plate_number)', 'El número de placa debe ser único.')
    ]