# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Cost Centers',
    'version': '11.0.0.1',
    'category': 'General',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Kopkarla - TBD',
    'description': """
    This is the module to manage cost center
    * Account
    * Sale 
    * Purchase
    * Fixed asset
    * Employee, department, and Employee expense
    """,
    'website': 'Ref.: https://www',
    "contributors":["Jupical Technologies Pvt. Ltd."],
    'depends': ['sale_expense',
                'purchase',
                'purchase_requisition',
                'stock',
                # 'account_asset_kopkarla',
                'hr','hr_expense',
                # 'sprogroup_purchase_request',
                # 'enhanced_purchase_request_loa',
                'account_analytic_kopkarla',],
    'data': [
        'security/ir.model.access.csv',
        'views/cost_center_view.xml',
        'views/sale_view.xml',
        'views/account_invoice_view.xml',
        'views/account_invoice_report.xml',
        'views/hr_employee_view.xml',
        'views/hr_department_view.xml',
        'views/hr_expenses_view.xml',
        # 'report/hr_expense_report.xml',
        'views/account_move.xml',
        'views/purchase_request.xml',
        'views/purchase_view.xml',
    ],
    'images': ['static/description/poster_image.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
