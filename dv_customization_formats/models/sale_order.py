from odoo import models, fields, api
import qrcode
import base64
from io import BytesIO

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    placa = fields.Char(string='Placa')

    price_url = fields.Char(string="Price URL")
    qr_code_image = fields.Binary(string="QR Code Image", compute="_compute_qr_code_image", store=False)
    show_qr_code = fields.Boolean(string="Print QR Code", default=True, store=True)

    technical = fields.Many2one("res.partner","Técnico",store=True)
    
    @api.onchange('placa')
    def _compute_partner(self):
        if self.placa:
            car_plate = self.env['car.plate'].search([('plate_number', '=', self.placa)], limit=1)
            if car_plate:
                self.partner_id = car_plate.partner_id.id
            else:
                self.partner_id = False

    def _get_report_base_filename(self):
        res = super()._get_report_base_filename()
        if self.company_id.country_id.code == 'PE' or self.company_id.country_id.code == 'US':
            res = 'dv_customization_formats.report_pe_price_document'
        return res

    # =========================================================================================

    @api.depends('show_qr_code')
    def _compute_qr_code_image(self):
        config = self.env['res.config.settings'].sudo().get_values()
        if self.state in ['draft','sent','sale']:
            if config['downloadable']:
                self.price_url = self.get_base_url() + self._get_share_url(redirect=True)
            elif config['custom']:
                if not self.price_url:
                    self.price_url = ""
            elif config['static']:
                base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                self.price_url = f"{base_url}/report/pdf/sale.report_saleorder/{self.id}"
            else:
                self.price_url = ''
        else:
            self.price_url = ''

        for record in self:
            if record.price_url and record.show_qr_code:
                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(record.price_url)
                qr.make(fit=True)
                img = qr.make_image(fill='black', back_color='white')
                buffer = BytesIO()
                img.save(buffer, format='PNG')
                record.qr_code_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
            else:
                record.qr_code_image = False

    @api.onchange('show_qr_code')
    def _onchange_show_qr_code(self):
        if self.show_qr_code:
            self._compute_qr_code_image()
