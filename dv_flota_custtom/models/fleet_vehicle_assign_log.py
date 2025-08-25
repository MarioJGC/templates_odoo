from odoo import api, fields, models

class FleetVehicleAssignationLog(models.Model):
    _inherit = "fleet.vehicle.assignation.log"
    _description = "Drivers history on a vehicle"
    _order = "create_date desc, date_start desc"

    vehicle_id = fields.Many2one(
        'fleet.vehicle', 
        string="Vehicle", 
        required=True, 
        ondelete='cascade'  # Permite eliminar el vehículo y sus logs asociados
    )
