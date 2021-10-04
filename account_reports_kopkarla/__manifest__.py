# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Accounting Reports',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Financial and Analytic Accounting',
    'description': """
Accounting Reports
========================
Weekly Invoice Report Status
""",
    'website': 'https://tbdigitalindo.co.id',
    'depends': [
        'account',
    ],
    'data': [
        'reports/account_invoice_weekly_report_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
