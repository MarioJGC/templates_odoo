# Importacones de Culqi
from odoo.http import request
from odoo import http
from odoo.exceptions import ValidationError
from odoo import SUPERUSER_ID

import requests, json

class CulqiController(http.Controller):

    @http.route('/payment/culqi/render_form', type='http',auth='public', website=True, csrf=False)
    def render_form(self, **data):

        if '__website_sale_last_tx_id' not in request.session:
            raise ValidationError('¡ERROR!\n Intente de nuevo o avise a su administrador de sistemas.')
        
        transaction_id = request.session['__website_sale_last_tx_id']
        obj_transaction = request.env['payment.transaction'].sudo().browse(int(transaction_id))

        values = {
            'public_key': obj_transaction.provider_id.culqi_public_key,
            'private_key': obj_transaction.provider_id.culqi_private_key,
            'reference': obj_transaction.reference,
            'amount': round(float(data.get('amount', 0000)) * 100,2),
            'currency': data.get('currency','PEN'),
        }

        return request.render('payment_culqi.culqi_form_template', values)

    @http.route('/payment/culqi/process_payment', type='json', methods=['POST'], auth='public', csrf=False, website=True)
    def process_payment(self, **kwargs):

        token = kwargs.get('token')
        email = kwargs.get('email')

        private_key = kwargs.get('private_key','')
        currency_code = kwargs.get('currency')
        amount_to_payment = kwargs.get('amount',0)
        reference = kwargs.get('reference')

        url = "https://api.culqi.com/v2/charges"

        payload = {
            "amount": amount_to_payment,
            "currency_code": currency_code,
            "email": email,
            "source_id": token,
            "capture": True,
            "description": reference,
            "installments": 0,
            "metadata": {
                'order_id': reference
            }
        }

        headers = {
            "Authorization": "Bearer " + private_key,
            "content-type": "application/json"
        }

        response = requests.request("POST", url, json=payload, headers=headers)

        if response.status_code == 201:

            data = {
                'amount': round((amount_to_payment / 100),2),
                'currency': currency_code,
                'reference': reference,
                'state': 'done',
                'redirect_url': '/payment/status'
            }

            request.env['payment.transaction'].with_user(SUPERUSER_ID).sudo()._handle_notification_data('culqi',data)
            return data

        else:
            response_data = json.loads(response.text)
            data = {
                'message': response_data['merchant_message'] if response_data['merchant_message'] else 'Credenciales invalidas o fondos insuficientes.'
            }
            
            return data
