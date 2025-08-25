from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_open_url(self):
        return {
            "type": "ir.actions.act_url",
            "url": "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio",
            "target": "new"
        }
