{
    'name': 'PE: Tipo de cuentas bancarias y CCI',
    'summary': 'Agrega tipos de cuentas bancarias peruanas y el campo CCI en las cuentas bancarias.',
    'version': '17.0',
    
    'author': 'Develogers',
	'website': 'https://develogers.com',
	'support': 'https://develogers.com/helpdesk',
	'live_test_url': 'https://wa.link/2cc9dn',
	'license': 'Other proprietary',
    
    'category': 'Localization',
    'version': '17.0',
    
    'currency': 'USD',
    'price': 19.99,
    
    'depends': [
        'base'
    ],
    
    'data': [
        'views/res_bank_views.xml',
        'views/res_partner_bank_views.xml',
    ],
    
    'installable': True,
    'auto_install': False,
}
