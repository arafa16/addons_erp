{
  'name': 'Enhanced Sales Approval',
  'author': 'odooindonesia.id',
  'version': '0.1',
  'depends': [
    'sale',
    'enhanced_sales_ttd',
    # 'enhanced_sales_agreement',
    'enhanced_sales_attribute',
    'enhanced_sales_project',
    'hr'
  ],
  'data': [
    'views/master_ttd.xml',
    'views/employee_tab.xml',
    'data/mail.template.csv',
    'views/config_views.xml',
    'security/security.xml',
    'security/ir.model.access.csv',
    'views/button_approval.xml',
    'print/print_so.xml',
    # 'views/so_loa.xml'
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Sales',
  'summary': 'Enhanced Sales Approval',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Enhanced Sales Approval'
}