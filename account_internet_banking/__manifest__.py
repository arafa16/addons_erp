# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Accounting Internet Banking',
    'version': '1.0',
    'category': 'Accounting',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Financial and Internet Banking',
    'description': """
Accounting - Internet Banking
========================
""",
    'website': 'https://www.cubicerp.com',
    'depends': [
        'account_kopkarla',
    ],
    'data': [
        'data/ir_sequence.xml',
        'views/payment_journal_views.xml',
        'views/payment_bank_batch_views.xml',
        'views/report_batch_payment.xml',
        'views/res_config_settings_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
