# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################



{
    'name': 'Expense Management Enhancement',
    'version': '11.0.0.1',
    'summary': 'Expense Advance Request - Employee',
    'description': """
    Managing enhancement of Expense Management:
    ===========================================
Expense Advance Request - Employee
Expense Advance
Created Menus :
employee Expense Advance
advance
employee advance
Expenses/Expense Advances
Expenses/Expense Advances/Expense Advance Requests
Expenses/Expense Advances/Advance to Approve
Expenses/Expense Advances/Advance to Pay
Defined Reports
            """,
    'license': 'Other proprietary',
    'category': 'Human Resources',
    'support': 'contact',
    'images': ['static/description/img1.jpg'],
    'author': 'TBD Team',
    'website': 'www',
    'depends': ['hr_expense', 'cost_centers_kopkarla'], #, 'board'],
    'data': ['security/hr_advance_security.xml',
             'security/ir.model.access.csv',
             'data/expense_sequence_data.xml',
             'wizard/hr_advance_payment.xml',
             'wizard/hr_expense_payment.xml',
             'views/hr_advance.xml',
             'views/hr_expense.xml',
             'views/hr_expense_sheet.xml',
             'views/res_config_settings_views.xml',
             'report/hr_advance_request_report.xml',
             'report/report_expense_sheet.xml',
             'views/dashboard_view.xml',
             ],
    'installable': True,
    'application': False,
}
