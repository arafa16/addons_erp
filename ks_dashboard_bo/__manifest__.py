# -*- coding: utf-8 -*-

{
    'name': 'Dashboard Ninja BO',
    'version': '11.0.0.1',
    'sequence': 105,
    'author': 'TBD Team',
    'maintainer': 'BOC',
    'category': 'Hidden',
    'license': '',
    'summary': 'Dashboard Ninja BO',
   
    'depends': ['ks_dashboard_ninja'],
    'data': [
        'views/ks_dashboard_ninja_assets.xml',
        'views/ks_dashboard_ninja_item_view.xml',
    ],
    'qweb': [
        'static/src/xml/ks_dashboard_ninja_templates.xml',
        'static/src/xml/ks_dashboard_ninja_item_templates.xml',
    ],
    'installable': True,
    'auto_install': False,
}
