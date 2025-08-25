# -*- coding: utf-8 -*-
from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    company_head_type = fields.Selection([
        ('lft', 'LFT'),
        ('wurfel', 'Wurfel'),
    ], string="Tipo encabezado", store=True)


