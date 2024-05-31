{
    "name": "Bill of Quantity",
    "version": "14.0.0.2",
    "depends": ['crm', 'crm_kopkarla', 'sale_crm', 'account'],
    "author": "TBD Team",
    "summary": "Bill of Quantity BOQ",
    "description": """
    Bill of Quantity On CRM
    Bill of Quantity On PR
    """,
    "website": "https://tbd.com",
    "data": [
        "security/rfi_security.xml",
        "security/ir.model.access.csv",
        "data/boq_sequence.xml",
        # "view/main_menu.xml",
        'wizards/rfi_select_vendor_view.xml',
        'view/bill_of_quantity_view.xml',
        'view/bill_of_quantity_line_view.xml',
        'view/crm_lead_views.xml',
        'view/rfi_view.xml',
        'view/rfi_history_view.xml',
        'view/cost_header_view.xml',
        'view/cost_code_view.xml',
        'reports/boq_mitra.xml',
        'reports/boq_customer.xml',
        'reports/boq_memo.xml',
    ],
    "auto_install": False,
    "installable": True,
}
