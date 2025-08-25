from odoo import _, api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Esta es una herencia de contactos
    def get_telecredito_identification_code(self):
        self.ensure_one()
        pe_vat_code = self.l10n_latam_identification_type_id.l10n_pe_vat_code
        if pe_vat_code == '1':
            identification_code = '1'
        elif pe_vat_code == '6':
            identification_code = '6'
        elif pe_vat_code == '4':
            identification_code = '3'
        elif pe_vat_code == '7':
            identification_code = '4'
        elif self.l10n_latam_identification_type_id.name == 'FIC':
            identification_code = '7'
        else:
            identification_code = ' '
        return identification_code

    def get_telecredito_partner_priority_bank_id(self):
        """
            Retorna una cuenta bancaria prioritaria para ser usada en el archivo de pago telecredito
        """
        self.ensure_one()
        
        if self.bank_ids:
            # Busca las cuentas bancarias del banco BCP que no sean interbancarias
            bcp_account_ids = self.bank_ids.filtered(lambda r: r.bank_id.bic == 'BCPLPEPL' and r.acc_number)
            if len(bcp_account_ids) > 1:
                # Si tiene varias cuentas bancarias del banco BCP, se prioriza la cuenta corriente
                priority_partner_bank_id = bcp_account_ids.filtered(lambda r: r.l10n_pe_cci == 'current_account')
            elif len(bcp_account_ids) == 1:
                # Si tiene una sola cuenta bancaria del banco BCP, se prioriza esa
                priority_partner_bank_id = bcp_account_ids[0]
            else:
                # Si no tiene cuentas bancarias del banco BCP, se prioriza una cuenta interbancaria de otro banco
                priority_partner_bank_id = self.bank_ids.filtered(lambda r: r.bank_id.bic != 'BCPLPEPL' and r.l10n_pe_cci)
        else:
            priority_partner_bank_id = self.env['res.partner.bank']            
        return priority_partner_bank_id
        
    def get_telecredito_company_priority_bank_id(self):
        """
            Retorna una cuenta bancaria prioritaria de la empresa para ser usada en el archivo de pago telecredito
        """
        self.ensure_one()
        priority_company_bank_id = self.env['res.partner.bank']            
        # Busca las cuentas bancarias del banco BCP que no sean interbancarias
        bcp_account_ids = self.company_id.bank_ids.filtered(lambda r: r.bank_id.bic == 'BCPLPEPL' and r.acc_type != 'interbank_account')
        if len(bcp_account_ids) > 1:
            # Si tiene varias cuentas bancarias del banco BCP, se prioriza la cuenta corriente
            priority_company_bank_id = bcp_account_ids.filtered(lambda r: r.acc_type == 'current_account')
        elif len(bcp_account_ids) == 1:
            # Si tiene una sola cuenta bancaria del banco BCP, se prioriza esa
            priority_company_bank_id = bcp_account_ids[0]
        return priority_company_bank_id