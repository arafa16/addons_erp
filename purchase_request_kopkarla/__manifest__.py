# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Purchase Request',
    'version': '11.0',
    'category': 'Purchase',
    'author':'odooindonesia.id',
    'description': """
Use Purchase Request module for requesting product.
    """,
    'summary': 'Purchase request type',
    'website': 'https://www.tbdigitalindo.co.id',
    'depends': ['sprogroup_purchase_request','cost_centers_kopkarla',
                'account_analytic_kopkarla','account_budget_kopkarla'],
    'data': [
        'views/purchase_request_type_view.xml',
        'views/purchase_request_view.xml',
        'data/purchase_request_type_data.xml',
        'security/purchase_request_type_security.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 105,
    'license': 'AGPL-3',
}
