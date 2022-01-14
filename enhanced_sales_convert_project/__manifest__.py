{
  'name': 'Sales Order Convert to Project',
  'author': 'odooindonesia.id',
  'version': '0.1',
  'depends': [
    'sale',
    'enhanced_sales_approval',
    'project_task_default_stage',
    'enhanced_sales_project',
    'enhanced_project_task_badges',
    'enhanced_project_customer_alias',
    'cost_centers_kopkarla'
  ],
  'data': [
    'views/sales_order.xml',
    'views/project_view.xml',
    'views/task_view.xml',
    'security/akses.xml',
    'views/filter_task.xml'
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Sales',
  'summary': 'Sales Order Convert to Project',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Sales Order Convert to Project'
}