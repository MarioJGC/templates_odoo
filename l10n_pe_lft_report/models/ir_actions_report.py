from odoo import models, fields, api


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _get_action_report_national_imported_merchandise(self):
        user = self.env.user
        if user.company_id.company_head_type == 'lft':
            return {
                'type': 'ir.actions.report',
                'name': 'Recepcion de mercadería',
                'model': 'stock.picking',
                'report_type': 'qweb-pdf',
                'report_name': 'l10n_pe_lft_report.report_merchandise_custom',
                'report_file': 'l10n_pe_lft_report.report_merchandise_custom',
                'print_report_name': 'Mercadería - %s - %s' % (object.partner_id.name or '', object.name),
                'binding_model_id': self.env.ref('stock.model_stock_picking').id,
                'binding_type': 'report',
                'paperformat_id': self.env.ref('l10n_pe_lft_report.paperformat_landscape_custom').id,
            }
        return False
