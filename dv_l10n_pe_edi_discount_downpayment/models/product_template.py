from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    l10n_pe_advance = fields.Boolean(string='Usado como Anticipo')

    l10n_pe_charge_discount = fields.Selection(
        selection=[('00', 'Descuentos que afectan la base imponible del IGV'),
                   ('01', 'Descuentos que no afectan la base imponible del IGV'),
                   ('02', 'Descuentos globales que afectan la base imponible del IGV'),
                   ('03', 'Descuentos globales que no afectan la base imponible del IGV'),
                   ('04', 'Descuentos globales por anticipos gravados que afectan la base imponible del IGV/IVAP'),
                   ('05', 'Descuentos globales por anticipos exonerados'),
                   ('06', 'Descuentos globales por anticipos inafectos'),
                   ('07', 'Factor de compensación - Decreto de urgencia N. 010-2004'),
                   ('20', 'Anticipo de ISC'),
                   ('45', 'FISE'),
                   ('46', 'Recargo al consumo y/o propinas'),
                   ('47', 'Cargos que afectan la base impnible del IGV'),
                   ('48', 'Cargos que no afectan la base imponible del IGV/IVAP'),
                   ('49', 'Cargos globales que afectan la base imponible del IGV/IVAP'),
                   ('50', 'Cargos globales que no afectan la base imponible del IGV/IVAP'),
                   ('51', 'Percepción venta interna'),
                   ('52', 'Percepción a la adquisición de combustible'),
                   ('53', 'Percepción realizada al agente de percepción con tasa especial'),
                   ('54', 'Factor de aportación - Decreto de urgencia N. 010-2004'),
                   ('61', 'Retención de renta por anticipos'),
                   ('62', 'Retención del IGV'),
                   ('63', 'Rentención de renta de segunda categoría')],
        string='Códigos de cargos o descuentos')

    @api.onchange('l10n_pe_advance')
    def checkbox_set_true_advance(self):
        for product in self:
            if product.l10n_pe_advance:
                product.global_discount = True
                product.l10n_pe_charge_discount = '04'
