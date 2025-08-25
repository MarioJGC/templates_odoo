{
    'name': 'Culqi Payment Acquirer',
    'version': '17.0',
    'author': 'Develogers',
    'website': 'https://develogers.com/',
    'summary': 'Payment Acquirer: Culqi Implementation',
    'category': 'eCommerce',
    'depends': ['payment','website','account'],
    'data': [
        'views/payment_provider_views.xml',
        'views/templates.xml',
        
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_culqi/static/src/js/card_lib.js',
            'payment_culqi/static/src/js/culqi_form.js',
            'payment_culqi/static/src/css/culqi.css',
        ],
    },
    'application': False,
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'uninstall_hook': 'uninstall_hook',
    'currency': 'USD',
    'price': 99.99
}