# -*- coding: utf-8 -*-
{
    'name': 'Signing',
    'version': '1.0',
    'author': "W Tim",
    'summary': """
    This module allows you to display signing location
    for approval
    """,
    'website': "",
    'description': """
        Signing
    """,
    'images': [],
    'category': 'Accounting',
    'depends': ['base_setup', 'account_invoicing', 'purchase'],
    'data': [
#        'views/account_invoice_report.xml',
        'views/sale_order_report.xml',
        'views/purchase_order_report.xml',
    ]
}
