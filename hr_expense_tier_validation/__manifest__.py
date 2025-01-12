# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Expense Tier Validation",
    "summary": "Extends the functionality of expense to "
               "support a tier validation process.",
    "version": "11.0.1.1.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/purchase-workflow",
    "author": "Smits Team",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr_expense",
        "hr_expense_kopkarla",
        "base_tier_validation",
        "account_budget_kopkarla",
    ],
    "data": [
        "views/hr_advance_view.xml",
        "views/hr_expense_sheet_view.xml",
    ],
}
