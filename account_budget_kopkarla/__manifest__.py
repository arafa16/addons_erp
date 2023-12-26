# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Budgets Management Enhancement',
    'version': '11.0.0.1',
    'summary': 'Kopkarla - TBD',
    'description': """
Managing enhancement of budget module in Odoo.
===============================================
Support following feature:
    * Add cost center
    """,
    'author': 'TBD Team',
    'website': 'http://.com',
    'category': 'Account',
    'sequence': 1,
    'depends': ['account_budget',
                'cost_centers_kopkarla',
                'enhanced_purchase_request_loa',
                'hr_expense_kopkarla',
                ],
    'data': [
        "views/account_budget_view.xml",
        "views/account_budget_menus.xml",
        "views/purchase_request_view.xml",
        # "views/purchase_order_view.xml",
        "views/account_analytic_view.xml",
        "views/res_users_view.xml",
        "views/res_config_settings_view.xml",
        "views/account_budget_request_approval.xml",
        "views/account_budget_request_release_approval.xml",
        "views/account_budget_available.xml",
        "views/account_budget_request_analysis.xml",
        "views/account_budget_adjustment.xml",
        "views/expense_budget_view.xml",
        "data/ir_sequence_data.xml",
        "security/ir.model.access.csv",
        "views/purchase_request_so_view.xml",
        "views/purchase_budget_request_view.xml",
        "wizard/multi_budget_view.xml",
    ],
    'installable': True,
    'application': False,
}
