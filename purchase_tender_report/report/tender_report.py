# -*- coding: utf-8 -*-
# Copyright (c) 2015-Present TidyWay Software Solutions. (<https://tidyway.in/>)

import pytz

from odoo import models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from pytz import timezone


class PurchaseTenderReportParser(models.AbstractModel):
    _name = 'report.purchase_tender_report.purchasetender_report'

    @api.model
    def convert_withtimezone(self, userdate):
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATETIME_FORMAT)
        tz_name = self.env.user.tz or 'UTC'
        user_datetime = pytz.utc.localize(user_date).astimezone(timezone(tz_name))
        user_datetime = user_datetime.replace(tzinfo=None)
        return user_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def convert_withtimezone_am_pm_format(self, userdate):
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATETIME_FORMAT)
        tz_name = self.env.user.tz or 'UTC'
        user_datetime = pytz.utc.localize(user_date).astimezone(timezone(tz_name))
        user_datetime = user_datetime.replace(tzinfo=None)
        #return user_datetime.strftime("%d %b %Y %I:%M %p")
        return user_datetime.strftime("%d %b %Y")

    @api.model
    def convert_dtfrmrt(self, userdate):
        user_date = datetime.strptime(userdate, DEFAULT_SERVER_DATE_FORMAT)
        return user_date.strftime("%d %b %Y")

    @api.model
    def get_best_supplier(self, tender, condition):
        total_purchases = \
            tender.purchase_ids.filtered(lambda x: x.state not in ('cancel'))
        total_purchases = total_purchases.sorted(key=lambda r: r.amount_total, reverse=True)
        if condition == 'min_three':
            total_purchases = total_purchases.sorted(key=lambda r: r.amount_total)

        count = 0
        supplier_list = []
        for purchase in total_purchases:
            count += 1
            if count <= 3:
                supplier_list.insert(count, purchase.partner_id.id)
        return supplier_list

    @api.model
    def get_supplier_name(self, supplier_id):
        partner = self.env['res.partner'].sudo().browse(supplier_id)
        return partner.name_get()[0][1]

    @api.model
    def last_purchased(self, product_id):
        lines = self.env['purchase.order.line'].search(
            [('product_id', '=', product_id),
             ('state', 'in', ['confirmed', 'purchase', 'done'])]).sorted(
            key=lambda l: l.order_id.date_order, reverse=True)
        last_unit_prices = lines[:1].price_unit and ("{:,}".format(lines[:1].price_unit))+ ' '+lines[:1].order_id.currency_id.symbol or '-'
        last_supplier = lines[:1].order_id.partner_id.name or '-'
        return last_unit_prices, last_supplier

    @api.model
    def get_report_values(self, docids, data=None):
        tender_records = self.env['purchase.requisition'].browse(data['ids'])
        return {
            'doc_ids': self._ids,
            'docs': tender_records,
            'data': data,
            'get_best_supplier': self.get_best_supplier,
            'tender_wise_value': self.tender_wise_value,
            'get_supplier_name': self.get_supplier_name,
            'last_purchased': self.last_purchased,
            'total_by_suppliers': self.total_by_suppliers
        }

    @api.model
    def total_by_suppliers(self, tender, supplier, condition):
        only_states_purchases = \
            tender.purchase_ids.filtered(lambda x: x.state not in ('cancel'))
        total_purchases = only_states_purchases.filtered(lambda x: x.partner_id.id == supplier)

        total_tender_products = [x.product_id.id for x in tender.line_ids if x.product_id]
        total_price_unit, total_vat_amount, total_subtotal, symbol = \
            0.0, 0.0, 0.0, ''
        for purchase in total_purchases:
            for line in purchase.order_line:
                if line.product_id and line.product_id.id in total_tender_products:
                    total_price_unit += line.price_unit
                    total_vat_amount += line.price_tax
                    total_subtotal += line.price_total
                    symbol = line.order_id.currency_id.symbol
        total_price_unit = str(total_price_unit and "{:,}".format(total_price_unit) or 0.0)+' '+ symbol
        total_vat_amount = str(total_vat_amount and "{:,}".format(total_vat_amount) or 0.0)+' '+ symbol
        total_subtotal = str(total_subtotal and "{:,}".format(total_subtotal) or 0.0)+' '+ symbol
        return total_price_unit, total_vat_amount, total_subtotal

    @api.model
    def tender_wise_value(self, tender, supplier, product_id, condition):
        only_states_purchases = \
            tender.purchase_ids.filtered(lambda x: x.state not in ('cancel'))
        total_purchases = only_states_purchases.filtered(lambda x: x.partner_id.id == supplier)

        price_unit, vat_amount, subtotal, symbol = 0.0, 0.0, 0.0, ''
        for purchase in total_purchases:
            for line in purchase.order_line:
                pproduct_id = line.product_id
                if pproduct_id and pproduct_id.id == product_id:
                    price_unit = line.price_unit
                    vat_amount = line.price_tax
                    subtotal = line.price_total
                    symbol = line.order_id.currency_id.symbol
                    break
        price_unit = str(price_unit and "{:,}".format(price_unit) or 0.0)+' '+ symbol
        vat_amount = str(vat_amount and "{:,}".format(vat_amount) or 0.0)+' '+ symbol
        subtotal = str(subtotal and "{:,}".format(subtotal) or 0.0)+' '+ symbol
        return price_unit, vat_amount, subtotal
