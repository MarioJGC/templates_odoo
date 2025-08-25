{
    'name': """
        Anticipos y Descuentos globales para Facturas Electrónicas - Perú |
        Advances and Global Discounts for Electronic Invoices - Peru
    """,

    'summary': """
        Permite enviar anticipos y descuentos globales en el XML de facturas electrónicas de Perú |
        Allows to send advances and global discounts in the XML of electronic invoices of Peru
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'LGPL-3',

    'category': 'Localization',
    'version': '17.0',

    'price': 99.99,
    'currency': 'USD',

    'depends': [
        'base',
        'sale',
        'l10n_pe_edi',
        'dv_account_move_global_discount',
    ],

    'data': [
        'data/2.1/edi_templates.xml',
        'views/account_move_views.xml',
        'views/product_template_views.xml',
    ],

    'demo': [
        'demo/product_template_demo.xml',
    ],
    
    'images': ['static/description/banner.png'],

    'application': False,
    'installable': True,
    'auto_install': True,
}
