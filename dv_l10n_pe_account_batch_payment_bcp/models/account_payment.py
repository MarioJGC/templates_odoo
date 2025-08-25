from odoo import _, api, fields, models
import re

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def get_bill_document_type_code(self):
        self.ensure_one()
        if self.reconciled_bill_ids:
            latam_document_code = self.reconciled_bill_ids[0].l10n_latam_document_type_id.code
        else:
            latam_document_code = False
        if latam_document_code == '01':
            document_type_code = 'F'
        elif latam_document_code == '07':
            document_type_code = 'N'
        elif latam_document_code == '08':
            document_type_code = 'C'
        elif self.move_id.l10n_latam_document_type_id.code == '03':
            document_type_code = 'B'
        # TODO consultar diego contabilidad if self.partner_id != self.env.company.partner_id
        #elif self.move_id.l10n_latam_document_type_id.name == 'Factura de la empresa':
        #    document_type_code = 'E'
        #elif self.move_id.l10n_latam_document_type_id.name == 'Nota crédito empresa':
        #    document_type_code = 'M'
        #elif self.move_id.l10n_latam_document_type_id.name == 'Cobranza':
        #    document_type_code = 'Z'
        else:
            document_type_code = 'D'
        
        return document_type_code
    
    
    def get_telecredito_payment_ref(self):
        self.ensure_one()
        payment_ref = re.sub(r'[^a-zA-Z0-9]', ' ', self.ref or '')
        # Si tiene mas de 2 espacios en el caracter, elimina el primer substring antes del primer espacio
        # F F001 43244
        if payment_ref.count(' ') == 2:
            # payment_ref = payment_ref.split(' ', 1)[1]
            # serial = payment_ref.split(' ')[1].rjust(8, '0')
            # telecredito_payment_ref = f"{payment_ref.split(' ')[0]} {serial}"
            telecredito_payment_ref = payment_ref.split(' ', 1)[1]
        else:
            telecredito_payment_ref = payment_ref
        # office_code = "A"
        return f"{telecredito_payment_ref}".replace(' ', '').rjust(15, '0')