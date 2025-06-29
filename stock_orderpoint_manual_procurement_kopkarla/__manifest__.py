# Copyright 2016-17 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Stock Orderpoint Manual Procurement Kopkarla",
    "summary": "Allows to create procurement orders from orderpoints instead "
               "of relying only on the scheduler.",
    "version": "11.0.0.0.0",
    "author": "Eficent, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/stock-logistics-warehouse",
    "category": "Warehouse Management",
    "depends": [
        "stock",
        "purchase",
        "purchase_requisition_kopkarla"
    ],
    "data": [
        'data/inventory_stock_monitoring_template.xml',
        "views/stock_warehouse_orderpoint_view.xml",
    ],
    "license": "AGPL-3",
    'installable': True,
    'application': False,
}
