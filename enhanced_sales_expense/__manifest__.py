{
  'name': 'Enhanced Sales Expense',
  'author': 'smits team',
  'version': '0.1',
  'depends': [
    'sale',
    'hr_expense',
    'hr_expense_kopkarla'
  ],
  'data': [
    'views/sales_order_views.xml',
    # 'views/hr_advance.xml',
    # 'views/hr_expense_sheet.xml',
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Project',
  'summary': 'Enhanced Sales Expense',
  'license': 'LGPL-3',
  'description': 'Enhanced Project Description'
}