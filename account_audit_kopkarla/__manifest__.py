# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Audit Report',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Financial and Analytic Accounting',
    'description': """
Accounting Audit Report
========================
""",
    'website': 'https://www.cubicerp.com',
    'depends': [
        'account',
        'account_kopkarla',
        'cost_centers_kopkarla',
        'account_analytic_kopkarla',
        'enhanced_invoiced_attribut',
    ],
    'data': [
        'views/invoice_payment_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
