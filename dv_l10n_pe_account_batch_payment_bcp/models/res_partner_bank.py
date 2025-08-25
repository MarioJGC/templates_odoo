from odoo import _, api, fields, models


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    def get_telecredito_bank_type_code(self):
        self.ensure_one()
        telecredito_bank_code = ' '
        bank_id_acc_type = self.acc_type
        if bank_id_acc_type == 'saving_account':
            telecredito_bank_code = 'A'
        elif bank_id_acc_type == 'current_account':
            telecredito_bank_code = 'C'
        elif bank_id_acc_type == 'master_account':
            telecredito_bank_code = 'M'
        elif bank_id_acc_type == 'interbank_account':
            telecredito_bank_code = 'B'
        else:
            telecredito_bank_code = ' '
            
        return telecredito_bank_code
    
    def get_telecredito_account_number(self):
        self.ensure_one()
        if self.acc_number:
            if self.bank_id.bic == 'BCPLPEPL':
                telecredito_account_number = self.acc_number
            else:
                telecredito_account_number = self.l10n_pe_cci
        else:
            telecredito_account_number = ' '
        return telecredito_account_number.ljust(20, ' ')

    def get_telecredito_account_number_integer(self):
        self.ensure_one()
        
        if self.acc_number:
            str_acc_number = self.acc_number.replace('-', '').replace(' ', '').replace('/', '')
            str_cci_number = self.l10n_pe_cci.replace('-', '').replace(' ', '').replace('/', '') if self.l10n_pe_cci else '0'
            if self.bank_id.bic == 'BCPLPEPL':
                formatted_acc_number = str_acc_number[3:]
            else:
                formatted_acc_number = str_cci_number[10:len(str_cci_number)]
        else:
            formatted_acc_number = '0'
        telecredito_account_number_integer = int(formatted_acc_number)
        return telecredito_account_number_integer
    
    def get_telecredito_bank_code(self):
        self.ensure_one()
        if self.bank_id.bic == 'BCPLPEPL':
            telecredito_bank_code = 'S'
        else:
            telecredito_bank_code = 'N'
        return telecredito_bank_code