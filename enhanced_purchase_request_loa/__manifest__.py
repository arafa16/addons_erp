{
  'name': 'Enhanced Purchase Request LOA',
  'author': 'odooindonesia.id',
  'version': '0.2',
  'depends': [
    'sprogroup_purchase_request',
    'enhanced_purchase_approval',
    'account',
    'enhanced_purchase_biding',
    'enhanced_purchase_request',
    'hr'
  ],
  'data': [
    'views/inherit_pr.xml',
    'views/menu_pr_loa.xml',
    'views/menu_buyer.xml',
    'views/menu_pr_loa_new.xml',
    'views/menu_pr_assman.xml',
    'views/inherit_pr_print.xml',
    'views/inherit_employee.xml'
  ],
  'qweb': [

  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Purchase',
  'summary': 'Enhanced Purchase Request LOA',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Enhanced Purchase Request LOA'
}