from odoo import api, fields, models, _

class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    # TODO
    # def _compute_terms(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency):
    