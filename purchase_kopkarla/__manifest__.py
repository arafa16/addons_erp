# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Purchase Management',
    'version': '11.0.0.1',
    'category': 'Purchases',
    'sequence': 1,
    'license': 'AGPL-3',
    'author': 'TBD Team',
    'summary': 'Purchase Received - Cost Center & Analytic Account',
    'description': """
This module is enhancemnet of Purchase Management.
===========================================================
It gives each transaction a cost center and an analytic account.
""",
    'website': 'https://',
    'depends': [
        'purchase',
        'enhanced_purchase_approval',
        # 'enhanced_purchase_tnc',
        'cost_centers_kopkarla',
    ],
    'data': [
        'security/purchase_security.xml',
        'wizard/purchase_make_invoice_advance_views.xml',
        'views/purchase_views.xml',
        'views/res_config_settings_views.xml',
        'views/payment_term_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
