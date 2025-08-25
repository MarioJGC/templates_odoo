from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    l10n_pe_is_withholding_line = fields.Boolean(
        string='Es apunte de retención', copy=False)
