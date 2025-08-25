# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import base64
from lxml import etree
from num2words import num2words

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_repr, float_round
from odoo.exceptions import UserError
from io import BytesIO

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None

class AccountMove(models.Model):
    _inherit = 'account.move'

    amount_undiscounted = fields.Float(
        string="Amount Before Discount",
        compute='_compute_amount_undiscounted', digits=0)

    amount_undiscounted_line = fields.Float(
        string="Amount Before Discount by line",
        compute='_compute_amount_undiscounted_line', digits=0)

    advance_payment = fields.Float(
        string="advance payment",
        compute='_compute_amount_advance_payment', digits=0)

    qr_code = fields.Binary("QR Code", compute='generate_qr_code')

    def _compute_amount_undiscounted(self):
        for invoice in self:
            total = 0.0
            for line in invoice.line_ids:
                total += (line.price_subtotal * 100)/(100-line.discount) if line.discount != 100 else (line.price_unit * line.quantity)
            self.amount_undiscounted = total

    def _compute_amount_undiscounted_line(self):
        for invoice in self:
            total = 0.0
            for line in invoice.line_ids:
                if line.product_id.discount_product:
                    total += -(line.price_unit * line.quantity)
            self.amount_undiscounted_line = total

    def _compute_amount_advance_payment(self):
        for invoice in self:
            total = 0.0
            for line in invoice.line_ids:
                if line.product_id == invoice.company_id.sale_down_payment_product_id:
                    total += -(line.price_unit * line.quantity)
            self.advance_payment = total


    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.l10n_latam_use_documents and self.company_id.country_id.code == 'PE':
            return 'l10n_pe_lft_report.report_invoice_document'
        return 'l10n_pe_lft_report.report_invoice_document' #super()._get_name_invoice_report()

    def get_total_amount_to_text(self):
        """Transform a float amount to text words on peruvian format: AMOUNT IN TEXT 11/100
        :returns: Amount transformed to words peruvian format for invoices
        :rtype: str
        """
        self.ensure_one()
        amount_i, amount_d = divmod(self.amount_total, 1)
        amount_d = int(round(amount_d * 100, 2))
        words = num2words(amount_i, lang='es')
        result = 'SON:%(words)s CON %(amount_d)02d/100 %(currency_name)s' % {
            'words': words,
            'amount_d': amount_d,
            'currency_name':  self.currency_id.full_name,
        }
        return result.upper()

    def generate_qr_code(self):
        for rec in self:
            if qrcode and base64:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=3,
                    border=4,
                )
                qr.add_data(f"{rec.company_id.vat}|")
                qr.add_data(f"{rec.company_id.partner_id.l10n_latam_identification_type_id.l10n_pe_vat_code}|")
                qr.add_data(f"{rec.name}|")
                qr.add_data(f"{rec.amount_total}")
                qr.make(fit=True)
                img = qr.make_image()
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code': qr_image})
                return qr_image