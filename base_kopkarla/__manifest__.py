# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP
#    Copyright (C) 2020 TBD ERP
#
##############################################################################

{
    'name': 'Base TBD',
    'version': '11.0.0.1',
    'sequence': 100,
    'author': 'TBD Team',
    'maintainer': 'TBD',
    'category': 'Hidden',
    'description': """
Menyesuaikan informasi company untuk Indonesia.
===================================================
""",
    'depends': ['base'],
    'data': [
        'ir/ir_sequence_view.xml',
        # 'module/module_view.xml',
        # 'res/res_partner_view.xml',
        'res/res_bank_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
}

