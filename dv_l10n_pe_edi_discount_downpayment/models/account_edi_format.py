from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _l10n_pe_edi_get_edi_values(self, invoice):
        values = super(AccountEdiFormat,
                       self)._l10n_pe_edi_get_edi_values(invoice)
        special_lines = invoice.invoice_line_ids.filtered(
            lambda l: not l.display_type == 'line_section' and l.price_subtotal < 0 and
            (l.product_id.l10n_pe_advance or l.product_id.global_discount)
        )
        if special_lines:
            filter_invoice_line_vals_list = []
            new_index = 1
            line_extension_amount = 0
            tax_inclusive_amount = 0
            for actual_line in values['invoice_line_vals_list']:
                if not actual_line['line'].product_id.l10n_pe_advance:
                    line_extension_amount += actual_line['line'].price_subtotal
                    tax_inclusive_amount += actual_line['line'].price_total
                if actual_line['line'] in special_lines:
                    continue
                actual_line['index'] = new_index
                filter_invoice_line_vals_list.append(actual_line)
                new_index += 1

            self._l10n_pe_edi_set_special_lines_vals(
                values, invoice, special_lines)
            values.update({
                'invoice_line_vals_list': filter_invoice_line_vals_list,
                'line_extension_amount': line_extension_amount,
                'tax_inclusive_amount': tax_inclusive_amount,
                'payable_amount': tax_inclusive_amount - values.get('total_advance', 0)
            })
        return values

    @staticmethod
    def _l10n_pe_edi_set_special_lines_vals(values, move_id, special_lines):
        """
        Filter and separate special lines (Example: Global discount and advance lines)
        """
        advance_lines_vals = []
        discount_lines_vals = []
        i = 1
        total_advance = 0.00
        total_discount = 0.00

        discount_percent_global = move_id.discount_percent_global / 100
        for line in special_lines:
            # Advance line
            if line.product_id.l10n_pe_advance:
                if not line.l10n_pe_advance_invoice:
                    raise ValidationError(
                        f'{line.product_id.name}: Nombre de Anticipo vácio.')
                if move_id.l10n_latam_document_type_id.code == '01':
                    document_type_id_code = '02'
                elif move_id.l10n_latam_document_type_id.code == '03':
                    document_type_id_code = '03'
                else:
                    document_type_id_code = move_id.l10n_latam_document_type_id.code or ''
                advance_line = {
                    'index': i,
                    'line': line,
                    'advance_name': line.l10n_pe_advance_invoice,
                    'partner_vat': move_id.partner_id.vat,
                    'company_vat': move_id.company_id.vat,
                    'company_type_document': move_id.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code,
                    'l10n_latam_document_type_id': document_type_id_code,
                    'datetime_document': move_id.invoice_date,
                    'tax_inclusive_amount': abs(line.price_total)
                }
                total_advance += advance_line['tax_inclusive_amount']
                advance_lines_vals.append(advance_line)
                i += 1

            # Discount global line
            if line.product_id.global_discount:
                product_id = line.product_id
                reason_code = product_id.l10n_pe_charge_discount or '00'
                discount_global_line = {
                    'line': line,
                    'discount_charge_indicator': 'false' if reason_code not in ['45', '46', '47'] else 'true',
                    'discount_allowance_charge_reason_code': reason_code,
                    'discount_percent': discount_percent_global,
                    'discount_amount': abs(line.price_subtotal),
                    'base_amount': abs(line.price_subtotal / discount_percent_global),
                }
                if reason_code == '03':
                    total_discount += abs(line.price_subtotal)

                discount_lines_vals.append(discount_global_line)

        # if advance_lines_vals:
        values['advance_lines_vals'] = advance_lines_vals
        values['total_advance'] = total_advance

        # if discount_lines_vals:
        values['discount_lines_vals'] = discount_lines_vals
        values['total_discount'] = total_discount
