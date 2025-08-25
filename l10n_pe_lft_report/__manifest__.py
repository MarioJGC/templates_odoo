# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Configuring Reports',
    'summary': 'Este módulo personaliza la cabecera de los reportes de la compañía LFT de los modulos Cotización,  Orden de compra, Factura, Guía entre almacenes',
    'version': '17.0.0.10',
    'category': 'Reporting',
    'license': 'AGPL-3',
    'author': '',
    'website': '',
    'depends': ['base', 'web', 'acn_sale', 'sale_pdf_quote_builder', 'l10n_pe_edi', 'purchase', 'stock'],

    'data': [
        'report/paperformat_sale_order.xml',
        # 'report/purchase_order_templates.xml',
        # 'report/purchase_quotation_templates.xml',
        'report/report_stockpicking_operations.xml',
        'report/report_nat_inter_merchandise.xml',
        'report/report_service_order.xml',
        'views/group_report.xml',
        'views/general_report.xml',
        'views/general_report_purchase_order.xml',
        'views/general_report_stock_picking.xml',
        'views/sale_order_report.xml',
        'views/report_invoice.xml',
        'views/res_company_config_view.xml',
        'views/stock_picking_report.xml',
        'views/account_report.xml',
        'views/sale_report_views.xml',
        'views/general_report_merchandise.xml',
        'views/general_report_service_order.xml',
     ],
    'assets': {
        'web.assets_backend': [
            'l10n_pe_lft_report/static/src/css/custom_styles.css',
        ],
    },
    'installable': True,


}
