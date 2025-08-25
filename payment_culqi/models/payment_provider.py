from odoo import _, api, fields, models


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('culqi', 'Culqi')],
        ondelete={'culqi': 'set default'}
    )
    culqi_public_key = fields.Char(
        string='Llave pública',
        required_if_provider='culqi',
        groups='base.group_system'
    )
    culqi_private_key = fields.Char(
        string='Llave privada',
        required_if_provider='culqi',
        groups='base.group_system'
    )
    
    @api.model
    def _get_compatible_providers(self, *args, currency_id=None, **kwargs):
        """ Override of payment to unlist Culqi providers for unsupported currencies. """
        providers = super()._get_compatible_providers(*args, currency_id=currency_id, **kwargs)
        
        currency = self.env['res.currency'].browse(currency_id).exists()
        if currency and currency.name not in ('PEN', 'USD'):
            providers = providers.filtered(lambda p: p.code != 'culqi')

        return providers