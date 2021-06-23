# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Accounting Management',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Financial and Analytic Accounting',
    'description': """
Accounting Access Rights
========================
It gives the Administrator user access to all accounting features such as journal items and the chart of accounts.

It assigns manager and user access rights to the Administrator for the accounting application and only user rights to the Demo user.
""",
    'website': 'https://www.cubicerp.com',
    'depends': [
        'base',
        'account',
        'account_invoicing',
        'purchase'
        # 'account_asset_kopkarla',
    ],
    'data': [
        'data/report_paperformat.xml',
        'data/account_accountant_data.xml',
        'data/ir_sequence_data.xml',
        'security/account_accountant_security.xml',
        'views/account_accountant_templates.xml',
        'views/account_group_view.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_views.xml',
        'views/account_bank_statement_view.xml',
        'wizard/account_payment_tax_adjustment_view.xml',
        'views/payment_journal_views.xml',
        'views/payment_journal_reports.xml',
        'views/account_move_reports.xml',
        'views/account_view.xml',
        'views/account_move_line_tax.xml',
        'views/report_payment_journal.xml',
        'views/report_payment_voucher.xml',
        'views/report_account_move.xml',
        'views/res_config_settings_view.xml',
        'views/res_company.xml',
        # 'views/payment_journal_templates.xml',
        'security/ir.model.access.csv',
        'views/report_invoice.xml',
        'views/report_invoice_to_pay.xml',
        'views/account_report_payment_receipt_templates.xml',
    ],
    'demo': ['data/account_accountant_demo.xml'],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
