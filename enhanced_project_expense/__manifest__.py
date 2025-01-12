{
  'name': 'Enhanced Project Expense',
  'author': 'smits team',
  'version': '0.1',
  'depends': [
    'project',
    'hr_expense',
    'hr_expense_kopkarla'
    # 'cost_centers_kopkarla',
    # 'enhanced_sales_convert_project'
  ],
  'data': [
    'views/project_task.xml',
    'views/hr_advance.xml',
    'views/hr_expense_sheet.xml',
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Project',
  'summary': 'Enhanced Project Purchase Request',
  'license': 'LGPL-3',
  'description': 'Enhanced Project Description'
}