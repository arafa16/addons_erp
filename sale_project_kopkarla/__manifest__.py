# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Sale And Project Module Enhancement',
    'version': '11.0.0.1',
    'category': 'Sales',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Kopkarla - TBD',
    'description': """
    This is the module to manage sale module
    * Add project task analytic account
    """,
    'website': 'Ref.: https://www',
    'depends': ['project',
                'enhanced_sales_convert_project',
                'enhanced_sales_attribute',
                'sale','sales_team',
                'sprogroup_purchase_request',
                'cost_centers_kopkarla',
                'account'
                ],
    'data': [
        'views/reva_tabel.xml',
        'views/project_tabel.xml',
        'views/sale_view.xml',
        'views/sale_report.xml',
        'views/account_invoice_view.xml',
        'reports/sale_pr_po_views.xml',
        'reports/sale_costs_margin.xml',
        # 'reports/sale_report_margin_views.xml',
        'reports/sale_report_reva_views.xml',
        'security/ir.model.access.csv',
        'security/sale_security.xml',
    ],
    'images': ['static/description/poster_image.png'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
