# -*- coding: utf-8 -*-
{
	'name': 'Dashboard Ninja',

	'summary': """Dashboard Ninja for Odoo provides interactive dashboards and visual business data for CRM, Sales, Inventory, Accounting, HR, and other Odoo applications.
""",

	'description': """
Dashboard Ninja v11.0,
        Odoo Dashboard,
        Dashboard,
        Odoo apps,
        Dashboard app,
        HR Dashboard,
        Sales Dashboard,
        inventory Dashboard,
        Lead Dashboard,
        Opportunity Dashboard,
        CRM Dashboard,
        POS,
        POS Dashboard,
        Connectors,
        Web Dynamic,
        Report Import/Export,
        Date Filter,
        HR,
        Sales,
        Theme,
        Tile Dashboard,
        Dashboard Widgets,
        Dashboard Manager,
        Debranding,
        Customize Dashboard,
        Graph Dashboard,
        Charts Dashboard,
        Invoice Dashboard,
        Project management,
        ksolves,
        ksolves apps,
        ksolves india pvt. ltd.
        dashboard,
        odoo dashboard,
        odoo apps,
        all in one dashboard,
        dashboard odoo,
        dashboard items,
        multiple dashboards,
        dashboard menu,
        dashboard view,
        create multiple dashboards,
        multiple dashboard menu,
        edit dashboard items,
        dahsboard view,
""",

	'author': 'Ksolves India Ltd.',

	'license': 'OPL-1',

	'currency': 'EUR',

	'price': '422.35',

	'website': 'https://store.ksolves.com/',

	'maintainer': 'Ksolves India Ltd.',

	'live_test_url': 'https://dn15demo.kappso.com/web/demo_login',

	'category': 'Tools',

	'version': '11.0.8.3.4',

	'support': 'sales@ksolves.com',

	'images': ['static/description/Ks_Dn_AI.gif'],

	'depends': ['base', 'web', 'base_setup', 'bus', 'decimal_precision'],

	'data': ['security/ks_security_groups.xml', 'security/ir.model.access.csv', 'data/ks_default_data.xml', 'views/ks_dashboard_ninja_view.xml', 'views/ks_dashboard_ninja_item_view.xml', 'views/ks_dashboard_ninja_assets.xml', 'views/ks_dashboard_action.xml'],

	'demo': ['demo/ks_dashboard_ninja_demo.xml'],

	'qweb': ['static/src/xml/ks_dn_global_filter.xml', 'static/src/xml/ks_dashboard_ninja_templates.xml', 'static/src/xml/ks_dashboard_ninja_item_templates.xml', 'static/src/xml/ks_dashboard_ninja_item_theme.xml', 'static/src/xml/ks_widget_toggle.xml', 'static/src/xml/ks_dashboard_pro.xml', 'static/src/xml/ks_import_list_view_template.xml', 'static/src/xml/ks_quick_edit_view.xml'],

	'uninstall_hook': 'uninstall_hook',
}
