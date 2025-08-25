from odoo import api, fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    @api.model
    def _get_supported_account_types(self):
        rslt = super(ResPartnerBank, self)._get_supported_account_types()
        rslt.append(('wage', 'Sueldo'))
        rslt.append(('cts', 'CTS'))
        rslt.append(('saving_account', 'Cuenta de Ahorros'))
        rslt.append(('current_account', 'Cuenta Corriente'))
        rslt.append(('master_account', 'Cuenta Maestra'))
        return rslt

    # OVERRIDE
    @api.depends('acc_number')
    def _compute_acc_type(self):
        """
        TODO: De momento hacemos que esta funcion no haga nada si el pais es de peru
        """
        no_peru = self.filtered(lambda x: x.company_id.country_id.code != 'PE')
        super(ResPartnerBank, no_peru)._compute_acc_type()
        peru = self - no_peru
        for bank in peru:
            bank.acc_type = bank.acc_type if bank.acc_type else 'saving_account'

    # Se usa en forma de campo y no por tipo (acc_type) para que sea compatible con el flujo de pagos en Perú (proveedores y planilla)
    l10n_pe_cci = fields.Char(string='Código de Cuenta Interbancario (CCI)',
                              help='Utilizado para transferencias interbancarias en Perú.')
