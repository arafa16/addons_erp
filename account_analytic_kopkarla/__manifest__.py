# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Account Analytic Enhancement',
    'version': '11.0.0.1',
    'summary': 'Kopkarla - TBD',
    'category': 'Account',
    'sequence': 1,
    'license': 'AGPL-3',
    'author': 'TBD Team',
    "contributors": ["Odoo Community Association (OCA)"],
    'website': 'https://www.github.com/OCA/account-analytic.git',
    'depends': [
        'account_kopkarla',
        'analytic',
        'sprogroup_purchase_request',
        'enhanced_purchase_request_loa',
        'project',
    ],
    'data': [
        'views/account_analytic_account_view.xml',
        'views/account_asset_view.xml',
        'views/purchase_request.xml',
        'views/purchase_views.xml',
        'views/sales_views.xml',
        'views/hr_employee_view.xml',
        'views/hr_department_view.xml',
        'data/res_config_settings_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
