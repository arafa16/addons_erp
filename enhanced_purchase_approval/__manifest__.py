{
  'name': 'Enhanced Purchase Order LOA',
  'author': 'odooindonesia.id',
  'version': '0.1',
  'depends': [
    'hr',
    'enhanced_sales_ttd',
    'purchase',
    'purchase_requisition'
  ],
  'data': [
    'views/master_ttd.xml',
    'views/inherit_employee_ttd.xml',
    'views/inherit_purchase_order.xml',
    'views/inherit_purchase_order_line.xml',
    'security/ir.model.access.csv',
    'report/inherit_print.xml',
    'data/mail.template.csv'
  ],
  'qweb': [

  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Purchase',
  'summary': 'Enhanced Purchase LOA',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Enhanced Purchase Order LOA'
}