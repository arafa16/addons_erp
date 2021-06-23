# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Stock Module Enhancement',
    'version': '11.0.0.1',
    'category': 'Warehouse',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Kopkarla - TBD',
    'description': """
    This is the module to manage stock module
    * Add cost center on stock.picking, stock.move, stock.move.line
    * Add analytic account on stock.picking, stock.move, stock.move.line
    """,
    'website': 'Ref.: https://www',
    'depends': [
        'stock',
        'stock_account',
        'enhanced_project_mr',
        'cost_centers_kopkarla',
    ],
    'data': [
        'views/setting.xml',
        'views/stock_picking_view.xml',
        'views/stock_inventory_views.xml',
    ],
    'images': ['static/description/poster_image.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
