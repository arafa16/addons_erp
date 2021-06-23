# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solutions. (<https://tidyway.in/>)

{
    'name': 'Purchase Tender / Bid Supplier Price Comparision',
    'version': '1.0',
    'category': 'purchase',
    'summary': 'Bid Report| Requisition Report | Tender Report | Comparision Report',
    'description': """
Purchase Tender Comparision Report.
=====================================
    """,
    'author': 'TidyWay',
    'website': 'http://www.tidyway.in',
    'depends': ['purchase_requisition'],
    'data': [
            'security/tender.xml',
            'views/tender_report.xml',
            'wizard/tender_report.xml',
            'views/menu.xml'
             ],
    'price': 99,
    'currency': 'EUR',
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
    'application': True,
    'images': ['images/tender.png'],
    'live_test_url': 'https://youtu.be/bZpu3lvAuf8'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
