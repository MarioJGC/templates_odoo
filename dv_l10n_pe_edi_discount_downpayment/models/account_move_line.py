from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_pe_advance_invoice = fields.Char(string='Factura anticipo Relacionada', copy=False)
