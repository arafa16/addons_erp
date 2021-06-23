# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Purchase Agreements',
    'version': '11.0.0.1',
    'summary': 'Kopkarla - TBD',
    'category': 'Purchases',
    'sequence': 1,
    'license': 'AGPL-3',
    'author': 'TBD Team',
    'summary': 'Financial and Analytic Accounting',
    'description': """
This module is enhancemnet of Purchase Agreements.
===========================================================
It gives each transaction a cost center and an analytic account.
""",
    'website': 'https://',
    'depends': [
        'purchase_requisition',
        'cost_centers_kopkarla',
    ],
    'data': [
        'views/purchase_requisition_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
