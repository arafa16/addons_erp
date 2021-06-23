{
  'name': 'Modul Help Desk',
  'author': 'odooindonesia.id',
  'version': '0.1',
  'depends': [
    'mail'
  ],
  'data': [
    'views/helpdesk.xml',
    'security/ir.model.access.csv',
    'security/security.xml',
    'data/mail.template.csv'
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Helpdesk',
  'summary': 'Help Desk',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Modul Help Desk'
}