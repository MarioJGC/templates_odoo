from odoo.addons.payment.tests.common import PaymentCommon


class CulqiCommon(PaymentCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.culqi = cls._prepare_provider('culqi', update_values={
            'culqi_public_key': 'dummy',
            'culqi_private_key': 'dummy'
        })
        cls.provider = cls.culqi
        cls.country_peru = cls.env.ref('base.pe')
        cls.currency = cls._prepare_currency('PEN')
        cls.default_partner.write({
            'country_id': cls.country_peru.id,            
        })