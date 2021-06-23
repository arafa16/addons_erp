# -*- coding: utf-8 -*-
{
    'name': 'Convert number to words',
    'version': '2.0',
    'author': "W Tim",
    'summary': """
    This module allows you to convert number to words """,
    'website': "",
    'description': """
        Convert invoice amount to text
    """,
    'images': ['static/description/convert.jpg'],
    'category': 'Accounting',
    'depends': ['base_setup', 'account_invoicing', 'purchase'],
    'data': [
        'views/account_invoice_view.xml',
        'views/account_invoice_report.xml',
        'views/account_config_setting_view.xml',
        'views/sale_order_view.xml',
        'views/sale_order_report.xml',
        'views/purchase_order_view.xml',
        'views/purchase_order_report.xml',
    ]
}
