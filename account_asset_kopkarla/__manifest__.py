# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP, Enterprise and Government Management Software
#    Copyright (C) 2020 TBD ERP (<http://>).
#
##############################################################################

{
    'name': 'Assets Management Enhancement',
    'version': '11.0.0.1',
    'category': 'Account',
    'sequence': 1,
    'author': 'TBD Team',
    'license': 'AGPL-3',
    'summary': 'Kopkarla - TBD',
    'description': """
Managing enhancement of asset module in Odoo.
===============================================
Support following feature:
    * Add asset type on purchase invoice
    * Add asset on purchase invoice 
    * Add journal entry on asset view
    * Add asset on purchase invoice
    * Reclass asset to new / other asset
    * Reclass asset to other asset category
    * Add asset disposal
    """,
    'website': 'http://.com',
    'depends': [
                # 'account',
                'account_kopkarla',
                'account_asset',
                'cost_centers_kopkarla',],
    'data': [
        "views/account_asset_category_view.xml",
        "views/account_invoice_view.xml",
        "views/account_view.xml",
        "wizards/account_asset_reclass_view.xml",
        "wizards/account_asset_disposal_wizard_view.xml",
        "views/account_asset_views.xml",
        "views/account_asset_sale_views.xml",
        "views/account_asset_disposal_views.xml",
        "views/account_asset_revaluation_views.xml",
        "views/account_asset_depreciation_views.xml",
        "views/account_asset_reclass_views.xml",
        "views/account_asset_menus.xml",
        "reports/asset_balance_report_view.xml",
        # "data/sequences.xml",
        "security/ir.model.access.csv"
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
