{
    'name': "CRM Activities",

    'summary': """
        Modulo personalizado para funcionalidades en la actividades del módulo CRM de Odoo.""",

    'author': 'Develogers',
    'website': 'https://develogers.com',
    'support': 'especialistas@develogers.com',
    'live_test_url': 'https://wa.me/message/NN37LBBZC5TQA1',
    'license': 'Other proprietary',

    'category': 'Other',
    'version': '17.1',

    'depends': ['base',
                'crm',
                'mail',
                'dv_crm_project_custom',
                'dv_crm_new_custom'
                ],

    "data": [
        
        # Security
        "security/ir.model.access.csv",
        # Views
        "views/mail_activity_views.xml",
        "views/mail_activity_schedule_views.xml",
        "views/mail_activity_views.xml",
        "views/message_activity_done.xml",
    ],

    'assets':{
        'web.assets_backend': [
            'dv_crm_activities/static/src/js/activity_button_pacth.js',
            'dv_crm_activities/static/src/js/activity_patch.js',
            'dv_crm_activities/static/src/activity/**/*',
        ]
    },

    'images': ['static/description/icon.png'],
    
    'application': True,
    'installable': True,
    'auto_install': False,
}

