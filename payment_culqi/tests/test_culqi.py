from odoo.tests import tagged

from odoo.addons.payment.tests.http_common import PaymentHttpCommon
from odoo.addons.payment_culqi.tests.common import CulqiCommon


@tagged('post_install', '-at_install')
class CulqiTest(CulqiCommon, PaymentHttpCommon):

    def test_payment_request_payload_values(self):
        tx = self._create_transaction(flow='redirect')
        
        self.assertEqual(tx.currency_id.name, 'PEN')
        self.assertEqual(tx.amount, 1111.11)
