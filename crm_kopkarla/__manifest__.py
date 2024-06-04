{
    "name": "CRM Kopkarla",
    "version": "14.0.0.2",
    "depends": ['crm', 'cost_centers_kopkarla','account_analytic_kopkarla','enhanced_sales_project'],
    "author": "TBD Team",
    "summary": "CRM",
    "description": """
    """,
    "website": "https://tbd.com",
    "data": [
        'security/presales_security.xml',
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/crm_order_type_views.xml',
        # 'reports/crm_opportunity_sale_report_views.xml',
        'reports/sale_invoice_report_views.xml',
    ],
    "auto_install": False,
    "installable": True,
}
