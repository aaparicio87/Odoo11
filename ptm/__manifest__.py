# -*- coding: utf-8 -*-
{
    'name': "Plan de Trabajo Mensual",

    'summary': """
       Gestiona planes de trabajos del mes""",

    'description': """
        * Modelo 2
        * Modelo 3
        * Resumen """,

    'author': "EPIA ONCE",
    'website': "https://www.epiaonce.cu",

  
    'category': 'Extra Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['calendar', 'hr', 'contacts'],

    # always loaded
    'data': [
        'views/plan_mensual_view.xml',
        'reports/reporte_modelo.xml',
        'wizards/report.xml',
        'wizards/attendees_department_view.xml',
        'views/attendees_ocd_view.xml',
        #'security/security.xml',
    ],

    'application': True,
    'installable': True,
}