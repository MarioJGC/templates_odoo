{
    'name': """
        Porcentaje de Descuento global en Facturas |
        Global Discount Percentage in Invoices
    """,

    'summary': """
        Calcula el porcentaje de descuento global y el monto de descuento global en facturas |
        Calculate the percentage of global discount and the amount of global discount in invoices
    """,

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'https://develogers.com/helpdesk',
    'live_test_url': 'https://wa.link/2cc9dn',
    'license': 'LGPL-3',

    'category': 'Accounting',
    'version': '17.0',

    'price': 24.99,
    'currency': 'USD',

    'depends': [
        'base',
        'account',
    ],

    'data': [
        'views/account_move_views.xml',
        'views/product_template_views.xml'
    ],

    'images': ['static/description/banner.png'],

    'application': False,
    'installable': True,
    'auto_install': False,
}
