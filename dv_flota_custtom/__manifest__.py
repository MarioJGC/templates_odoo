# -*- coding: utf-8 -*-
{
    'name': "Personalización para el módulo de flotas",

    'summary': """
        Módulo personalizado para el registro de vehiculos desde el módulo de contactos""",

    'author': 'Develogers',
	'website': "https://develogers.com/",
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://demo.develogers.com',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    'depends': [
        'base',
        'fleet',
        'dv_customization_formats'
    ],

    "data": [
        "views/fleet_vehicle_views.xml",
        "views/contacts_form_views.xml",
        "views/account_move_views.xml"
    ],
    
    'images': ['static/description/icon.png'],
    'application': True,
    'installable': True,
    'auto_install': False,
}

