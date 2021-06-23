{
  'name': 'Enhanced Purchase Order Rating',
  'author': 'odooindonesia.id',
  'version': '0.1',
  'depends': [
    'purchase',
    'sprogroup_purchase_request',
    'account'
  ],
  'data': [
    'views/purchase_order.xml',
    'views/res_partner.xml',
    'views/rating_raport.xml',
    'security/ir.model.access.csv'
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Purchase',
  'summary': 'Enhanced Vendor Rating',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Enhanced Purchase Vendor Ratring'
}