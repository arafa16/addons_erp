# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle 
#
##############################################################################
{
    'name': 'All in one Cancel Sale,Purchase,Picking', 
    'version': '11.0.2.5',
    'sequence': 1, 
    'category': 'Generic Modules/Warehouse', 
    'summary': 'odoo App will allow to cancel sale,purchase,picking,invoice in done state in single click',
    'description':  
        """ 
        odoo App will allow to cancel sale,purchase,picking,invoice in done state in single click
        
        Tags:
        sale cancel, picking cancel, purchase cancel , cancel order, cancel shipment, cancel invoice, 
        Cancel sale order, cancel qutation, Cancel picking , cancel purchase order, cancel orders, cancel delivery order,
        cancel stock moves, cancel stock quants
 
    All in one Cancel Sale,Purchase,Picking
    Odoo cancel sale
    Odoo cancel purchase
    Odoo cancel picking
    Odoo All in one Cancel Sale,Purchase,Picking
    Cancel sale in odoo
    Cancel purchase in odoo
    Cancel picking in odoo
    odoo apps will help you to cancel sale order, purchase Order, picking, shipment and invoice after done state in odoo
    cancel sale, picking, purchase order into done state in odoo 
    Cancel button option in Picking,Sale, invoice , Purchase order in odoo
    cancel picking or sale order , relevant stock move will also canceled
    Cancel Stock Picking
    Cancel & Reset Picking
    Cancel Sales Order In Odoo
    Cancel purchase order in odoo
    Cancel Delivery Orders
    Stock Picking Cancel
All in one Cancel Sale,Purchase,Picking

Odoo cancel sale

Odoo cancel purchase

Odoo cancel picking

Odoo All in one Cancel Sale,Purchase,Picking

Cancel sale in odoo

Cancel purchase in odoo

Cancel picking in odoo

odoo apps will help you to cancel sale order, purchase Order, picking, shipment and invoice after done state in odoo

cancel sale, picking, purchase order into done state in odoo

Cancel button option in Picking,Sale, invoice , Purchase order in odoo

cancel picking or sale order , relevant stock move will also canceled

Cancel Stock Picking

Cancel & Reset Picking

Cancel Sales Order In Odoo

Cancel purchase order in odoo

Cancel Delivery Orders

Stock Picking Cancel

Odoo All in one Cancel Sale,Purchase,Picking

All in one Cancel

Odoo all in one Cancel

Manage all in one cancel

Odoo manage all in one cancel

All in one cancel sale

Odoo all in one cancel sale

All in one Cancel Purchase

Odoo all in one Cancel Purchase

All in one Cancel Picking

Odoo All in one Cancel Picking

Manage all in one Cancel Sale

Odoo Manage All in one Cancel sale

Manage all in one Cancel Purchase

Odoo Manage all in one Cancel Purchase

Manage all in one Cancel Picking

Odoo manage All in one Cancel Picking

Allow user to cancel sale, picking, purchase order into done state in odoo

Odoo Allow user to cancel sale, picking, purchase order into done state in odoo

Added Cancel button option in Picking,Sale, invoice , Purchase order in odoo

Odoo Added Cancel button option in Picking,Sale, invoice , Purchase order in odoo

Once you cancel picking or sale order , relevant stock move will also canceled and it will do reverse to stock quant and manage stock back into odoo system

Odoo Once you cancel picking or sale order , relevant stock move will also canceled and it will do reverse to stock quant and manage stock back into odoo system

After cancel you can also move to order into set to draft and then user can also delete it in odoo

Odoo After cancel you can also move to order into set to draft and then user can also delete it in odoo

After picking is done and it's generated accounting entry for stock valuation into accounting then at the time of cancel relevant Journal entries and journal items all will be cancel so account also will be settle in odoo

Odoo After picking is done and it's generated accounting entry for stock valuation into accounting then at the time of cancel relevant Journal entries and journal items all will be cancel so account also will be settle in odoo

After cancel sale order and picking user can also cancel invoice and set it to draft

Odoo After cancel sale order and picking user can also cancel invoice and set it to draft

While cancel the sale/picking it will also manage stock quants according

Odoo While cancel the sale/picking it will also manage stock quants according

Only allowed user can do cancel process in all document like sale, purchase, picking in odoo

Odoo Only allowed user can do cancel process in all document like sale, purchase, picking in odoo        
        
    """,
    'depends': ['stock','sale_stock','account_kopkarla','account_cancel','purchase','sale', 'account_asset_kopkarla'],
    "data": [
        "security/security.xml",
        # "security/ir.model.access.csv",
        "views/stock_view.xml",
        "views/account_asset_sale_view.xml",
        "views/account_asset_disposal_view.xml",
        "views/account_asset_revaluation_view.xml",
        "views/account_asset_reclass_view.xml",
        "views/account_asset_depreciation_view.xml",
        "views/payment_journal_views.xml",
    ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    #author and support Details
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':49,
    'currency':'EUR',
    'live_test_url':'https://youtu.be/Z8jMlB5ADNg',
}

