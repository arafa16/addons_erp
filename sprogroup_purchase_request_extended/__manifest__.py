# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'PR Extended',
    'version': '11.1.0',
    'category': 'Purchases',
    'author':'W Tim',
    'description': """
Use Purchase Request module for requesting product.
    """,
    'summary': 'Create purchase request',
    'website': '',
    'images': ['static/description/icon.jpg'],
    'depends': ['mail','project'],
    'data': [
#        'data/sprogroup_purchase_request_data.xml',
#        'security/sprogroup_purchase_request_security.xml',
#        'security/ir.model.access.csv',
        'views/purchase_request_approval_email_template.xml',
    ],
    'depends': ['hr','purchase'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 106,
    'license': 'AGPL-3',
}
