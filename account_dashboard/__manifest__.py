# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP
#    Copyright (C) 2020 TBD ERP
#
##############################################################################

{
    'name': 'Accounting Management',
    'version': '11.0.0.1',
    'sequence': 101,
    'author': 'TBD Team',
    'maintainer': 'YKBUT',
    'category': 'Accounting',
    'summary': 'Conslidate data warehouse',
    'description': """
Accounting Module Enhancement
=============================
Tambah fitur konsolidasi
""",
    'website': 'https://www.tbdigitalindo.co.id',
    'depends': ['account_invoicing',
                'account',
                'base',
                ],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/populate.xml',
        'data/access_rule.xml',
        'views/cube_ratio_target_views.xml',
        'views/account_financial_report_view.xml',
        'views/cube_ratio_views.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
