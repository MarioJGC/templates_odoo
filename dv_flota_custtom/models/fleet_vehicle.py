from odoo import models, fields, api

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    nro_motor = fields.Char(string='Número de motor')

    def write(self, vals):
        res = super(FleetVehicle, self).write(vals)

        if not self.env.context.get('avoid_recursion'):  # Evitar recursión infinita
            for record in self:
                car_plate = self.env['car.plate'].search([('id_vehicle', '=', record.id)], limit=1)

                if car_plate:
                    update_vals = {}

                    # Solo actualizar los valores que realmente cambiaron
                    if 'model_year' in vals:
                        update_vals['model_year'] = vals['model_year']
                    if 'color' in vals:
                        update_vals['color'] = vals['color']
                    if 'nro_motor' in vals:
                        update_vals['nro_motor'] = vals['nro_motor']
                    if 'license_plate' in vals:
                        update_vals['plate_number'] = vals['license_plate']

                    if update_vals:  # Evita escribir si no hay cambios
                        car_plate.with_context(avoid_recursion=True).write(update_vals)

        return res

    def unlink(self):
        for record in self:
            car_plate = self.env['car.plate'].search([('id_vehicle', '=', record.id)], limit=1)
            if car_plate:
                # Desvincular la relación en lugar de eliminar directamente
                car_plate.with_context(skip_vehicle_unlink=True).write({'id_vehicle': False})
                car_plate.unlink()  # Luego eliminamos la placa

        return super(FleetVehicle, self).unlink()
