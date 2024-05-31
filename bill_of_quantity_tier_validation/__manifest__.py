# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Bill of Quantity Tier Validation",
    "summary": "Extends the functionality of Bill of Quantity to "
               "support a tier validation process.",
    "version": "11.0.1.1.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/purchase-workflow",
    "author": "Eficent, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "bill_of_quantity_kopkarla",
        "base_tier_validation",
    ],
    "data": [
        "views/bill_of_quantity_view.xml",
    ],
}
