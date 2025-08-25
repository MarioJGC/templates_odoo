from odoo import models, api, fields
from odoo.exceptions import ValidationError

class CarPlate(models.Model):
    _inherit = 'car.plate'

    model_id = fields.Many2one(
        'fleet.vehicle.model',
        'Model',
        tracking=True
    )

    model_year = fields.Char('Model Year', help='Año del modelo', store=True, readonly=False)
    color = fields.Char(help='Color del vehículo', store=True, readonly=False)
    nro_motor = fields.Char(string='Número de motor')

    id_vehicle = fields.Many2one('fleet.vehicle', string="Vehículo", ondelete="set null")

    @api.model
    def create(self, vals):
        car_plate = super(CarPlate, self).create(vals)

        fleet_vehicle_vals = {
            'driver_id': car_plate.partner_id.id,
            'license_plate': car_plate.plate_number,
            'model_id': car_plate.model_id.id,
            'model_year': car_plate.model_year,
            'color': car_plate.color,
            'nro_motor': car_plate.nro_motor,
            'company_id': self.env.user.company_id.id
        }

        vehicle = self.env['fleet.vehicle'].create(fleet_vehicle_vals)

        # Evitar recursión al asignar el id del vehículo
        car_plate.write({'id_vehicle': vehicle.id})

        return car_plate

    def write(self, vals):
        result = super(CarPlate, self).write(vals)

        for record in self:
            fleet_vehicle = record.id_vehicle
            if fleet_vehicle:
                fleet_vehicle.with_context(avoid_recursion=True).write({
                    'license_plate': vals.get('plate_number', record.plate_number),
                    'model_id': vals.get('model_id', record.model_id.id),
                    'model_year': vals.get('model_year', record.model_year),
                    'color': vals.get('color', record.color),
                    'nro_motor': vals.get('nro_motor', record.nro_motor),
                    'driver_id': vals.get('driver_id', record.partner_id.id),
                })

        return result

    def unlink(self):
        for record in self:
            if record.id_vehicle and not self.env.context.get('skip_vehicle_unlink'):
                record.id_vehicle.with_context(avoid_recursion=True).unlink()  # Evitamos recursión

        return super(CarPlate, self).unlink()