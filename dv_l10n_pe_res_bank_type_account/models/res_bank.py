from odoo import _, fields, models

class ResBank(models.Model):
    _inherit = 'res.bank'

    # NOTE: Tomado de Odoo v18
    l10n_pe_edi_code = fields.Char(
        'Código (PE)',
        help='Bank code assigned by the SUNAT to identify banking institutions.')