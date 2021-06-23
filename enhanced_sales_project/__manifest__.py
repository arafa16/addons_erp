{
  'name': 'Custom Sales Order Adding Jenis Project',
  'author': 'odooindonesia.id',
  'version': '0.1',
  'depends': [
    'sale',
    'enhanced_sales_attribute',
    'project'
  ],
  'data': [
    'views/project_tabel.xml',
    'data/enhanced.sales.project.tabel.csv',
    'views/jenis_tabel.xml',
    'data/enhanced.sales.jenis.tabel.csv',
    'views/pekerjaan_tabel.xml',
    'data/enhanced.sales.pekerjaan.tabel.csv',
    'security/security.xml',
    'security/ir.model.access.csv',
    'views/sales_order_tab.xml',
    'views/project_task_type.xml',
    'views/sales_order_area.xml',
    'print/print_so.xml'
  ],
  'qweb': [
  ],
  'sequence': 1,
  'auto_install': False,
  'installable': True,
  'application': False,
  'category': 'Sales',
  'summary': 'Custom Sales Order Adding Jenis Project',
  'license': 'LGPL-3',
  'website': 'https://odooindonesia.id',
  'description': 'Enhanced Modul Sales'
}