# -*- coding: utf-8 -*-
{
    'name': 'Account Asset Maintenance',
    'summary': 'Add relation between assets and equipments',
    'author': 'Onestein',
    'website': 'http://www.onestein.eu',
    'category': 'Accounting & Finance',
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account_asset',
        'maintenance',
        'mail',
    ],
    'data': [
        'views/account_asset.xml',
        'views/maintenance_equipment.xml',
        'views/account_config_setting_views.xml',
        'wizard/scrap_equipment.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
