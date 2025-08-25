# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
import base64
from lxml import etree
from num2words import num2words

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_repr, float_round
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_undiscounted_line = fields.Float(
        string="Amount Before Discount by line",
        compute='_compute_amount_undiscounted_line', digits=0)

    def _compute_amount_undiscounted_line(self):
        for order in self:
            total = 0.0
            for line in order.order_line:
                if line.product_id.discount_product:
                    total += -(line.price_unit * line.product_uom_qty)
            self.amount_undiscounted_line = total


