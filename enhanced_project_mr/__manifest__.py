{
  'name': 'Custom Project Material Request',
  'author': 'odooindonesia.id',
  'version': '0.1',
  'depends': [
    'project',
    'stock',
    'product',
    'sale',
    'enhanced_sales_convert_project',
    'enhanced_project_task_badges',
    'enhanced_project_cost',
    'enhanced_purchase_approval',
    'cost_centers_kopkarla',
    'account_analytic_kopkarla'
  ],
  'data': [
    'views/project_task_type.xml',
    'views/mr_product.xml',
    'views/mreturn_product.xml',
    'views/mreturn.xml',
    'security/ir.model.access.csv',
    'views/mr.xml',
    'views/mr_wizard.xml',
    'views/project_task.xml',
    'views/stockpicking.xml',
    'views/stock_move.xml',
    'views/spk_ready.xml'
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Project',
  'summary': 'Custom Project Material Request',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Custom Project Material Request'
}