# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Products Warehouse Maintained',
    'version': '11.0.0.0.0',
    'category': 'Product',
    'description': """
Use Purchase Request module for requesting product.
    """,
    'summary': 'Product warehouse maintained',
    'website': 'https://www.smits.co.id',
    'depends': ['product'],
    'data': [
        'views/product_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 106,
    'license': 'AGPL-3',
}
