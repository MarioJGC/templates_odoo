{
    'name': 'Reporte TXT Pagos masivos - Telecrédito BCP',
    
    'summary': "Este módulo emite los ficheros txt para el pago masivo a proveedores",
    
    'author': 'Develogers',
	'website': 'https://develogers.com',
	'support': 'https://develogers.com/helpdesk',
	'live_test_url': 'https://wa.link/2cc9dn',
	'license': 'Other proprietary',
    
    'category': 'Localization',
    'version': '17.0',

    'price': 249.99,
    'currency': 'EUR',


    'depends': [
        'account',
        'l10n_latam_base',
        'account_batch_payment',
        'dv_l10n_pe_res_bank_type_account',
    ],
    
    'data': [
        'data/account_payment_method_data.xml',
        'views/account_batch_payment_views.xml',
        'views/res_partner_views.xml',
        'views/menuitem_views.xml',
    ],
    
    'images': ['static/description/banner.png'],

    'auto_install': False,
    'application': True,
    'installable': True,
}
