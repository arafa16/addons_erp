# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP
#    Copyright (C) 2020 TBD ERP
#
##############################################################################
# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo import api, fields, models, _
import time, json
from odoo.http import request
from datetime import date, timedelta, datetime
import datetime
import pytz


class CubeAging(models.Model):
    _name = 'cube.aging'
    _description = "Cube Aging"

    name = fields.Char('Name')
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    line_ids = fields.One2many('cube.aging.line', 'aging_id', string='Lines')
    aging_ids = fields.One2many('cube.aging.balance', 'aging_id', string='Balance')
    # ap_ids = fields.One2many('cube.aging.ap', 'ap_id', string='A/P')
    # ar_ids = fields.One2many('cube.aging.ar', 'ar_id', string='A/R')
    # balance_ap = fields.Float(string='Balance A/P', compute="_comp_total_ap")
    # balance_ar = fields.Float(string='Balance A/R')

    def _comp_total_ap(self):
        for rw in self :
            balance = 0
            for row in rw.ap_ids :
                balance = row.balance

            rw.balance_ap = balance

    def days_cur_month(self):
        date_from = self.date_from
        date_to = self.date_to

        tgl_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        m_from = int(tgl_from.strftime("%m"))
        y_from = int(tgl_from.strftime("%Y"))

        tgl_to = datetime.datetime.strptime(date_to, '%Y-%m-%d')
        m_to = int(tgl_to.strftime("%m"))
        y_to = int(tgl_to.strftime("%Y"))

        # m = int(tgl_from.strftime("%m"))
        # y = int(tgl_from.strftime("%Y"))

        range_year = [] 
        if y_from < y_to: 
            range_year.extend(range(y_from, y_to)) 
            range_year.append(y_to)
        else :
            range_year.append(y_to)

        range_month = [] 
        if m_from < m_to: 
            range_month.extend(range(m_from, m_to)) 
            range_month.append(m_to)
        else:
            range_month.append(m_to)

        amount = 0
        for y in range_year :  
            for m in range_month :
                if m == 12 :
                    ndays = 31
                else :
                    ndays = (date(y, m+1, 1) - date(y, m, 1)).days

                d1 = date(y, m, 1)
                d2 = date(y, m, ndays)
                delta = d2 - d1
                balance_before = 0


                d1 = d1.strftime("%Y-%m-%d")
                d2 = d2.strftime("%Y-%m-%d")

                d1 = datetime.datetime.strptime(d1, '%Y-%m-%d')
                d2 = datetime.datetime.strptime(d2, '%Y-%m-%d')

                # for i in range(delta.days + 1) :
                for i in range(delta.days * 24 + 1):

                    j = int(i)+1
                    n = -1
                    
                    # date_val = (d1 + timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
                    datetime_val = (d1 + timedelta(hours=i)).strftime('%Y-%m-%d %H:%M:%S')

                    # date_to_val = (d1 + timedelta(days=j)).strftime('%Y-%m-%d %H:%M:%S')
                    datetime_to_val = (d1 + timedelta(hours=j)).strftime('%Y-%m-%d %H:%M:%S')

                    
                    datetimes = datetime.datetime.strptime(datetime_val, '%Y-%m-%d %H:%M:%S')
                    timezone = pytz.timezone(self._context.get('tz') or 'UTC')
                    datetimes = datetimes.astimezone(timezone)

                    # print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',datetimes.strftime('%H'))
                    hours = str(datetimes.strftime('%Y-%m-%d %H:%M:%S'))

                    dwh = self.env['dwh.trans'].sudo().search([('datetime_invoice', '>=', datetime_val),('datetime_invoice', '<', datetime_to_val)])
                    if dwh :
                        for row in dwh :
                            invoice_no = row.invoice_no
                            invoice_check = self.env['cube.aging.ap'].sudo().search([('invoice_no', '=', invoice_no)], limit=1)

                            if not invoice_check :
                                inv_amount = row.inv_amount * -1
                                pay_amount = row.pay_amount 
                                amount = amount + float(inv_amount) + float(pay_amount)

                                date_dwh_vals = {
                                    'ap_id' : self.id,
                                    'invoice_no' : invoice_no,
                                    'date' : row.datetime_invoice,
                                    'datetime' : row.datetime_invoice,
                                    'hours' : hours,
                                    'inv_amount' : inv_amount,
                                    'pay_amount' : pay_amount,
                                    'balance' : amount,
                                    }

                                # print('dwhtttttttttttttttttttttttttt',row.datetime_invoice,datetime_val,amount)
                                aging_dwh = self.env['cube.aging.ap'].sudo().create(date_dwh_vals)

                    else :
                        date_check = self.env['cube.aging.ap'].sudo().search([('datetime', '=', datetime_val)])
                        if not date_check :
                            date_ap_vals = {
                                'ap_id' : self.id,
                                'date' : datetime_val,
                                'datetime' : datetime_val,
                                'hours' : hours,
                                'inv_amount' : 0,
                                'balance' : amount,
                                }
                            
                            date_ar_vals = {
                                'ar_id' : self.id,
                                'date' : datetime_val,
                                'datetime' : datetime_val,
                                'inv_amount' : 0,
                                'balance' : amount,
                                }


                            aging_ap = self.env['cube.aging.ap'].sudo().create(date_ap_vals)
                            # aging_ar = self.env['cube.aging.ar'].sudo().create(date_ar_vals)

    def populate_schedule(self):
        date_from = self.date_from
        date_to = self.date_to

        tgl_from = datetime.datetime.strptime(date_from, '%Y-%m-%d')
        m_from = int(tgl_from.strftime("%m"))
        y_from = int(tgl_from.strftime("%Y"))

        tgl_to = datetime.datetime.strptime(date_to, '%Y-%m-%d')
        m_to = int(tgl_to.strftime("%m"))
        y_to = int(tgl_to.strftime("%Y"))

        # m = int(tgl_from.strftime("%m"))
        # y = int(tgl_from.strftime("%Y"))

        range_year = []
        if y_from < y_to:
            range_year.extend(range(y_from, y_to))
            range_year.append(y_to)
        else:
            range_year.append(y_to)

        range_month = []
        if m_from < m_to:
            range_month.extend(range(m_from, m_to))
            range_month.append(m_to)
        else:
            range_month.append(m_to)

        amount = 0
        for y in range_year:
            for m in range_month:
                if m == 12:
                    ndays = 31
                else:
                    ndays = (date(y, m + 1, 1) - date(y, m, 1)).days

                d1 = date(y, m, 1)
                d2 = date(y, m, ndays)
                delta = d2 - d1
                balance_before = 0

                d1 = d1.strftime("%Y-%m-%d")
                d2 = d2.strftime("%Y-%m-%d")

                d1 = datetime.datetime.strptime(d1, '%Y-%m-%d')
                d2 = datetime.datetime.strptime(d2, '%Y-%m-%d')

                # for i in range(delta.days + 1) :
                for i in range(delta.days * 24 + 1):

                    j = int(i) + 1
                    n = -1

                    # date_val = (d1 + timedelta(days=i)).strftime('%Y-%m-%d %H:%M:%S')
                    datetime_val = (d1 + timedelta(hours=i)).strftime('%Y-%m-%d %H:%M:%S')

                    # date_to_val = (d1 + timedelta(days=j)).strftime('%Y-%m-%d %H:%M:%S')
                    datetime_to_val = (d1 + timedelta(hours=j)).strftime('%Y-%m-%d %H:%M:%S')

                    datetimes = datetime.datetime.strptime(datetime_val, '%Y-%m-%d %H:%M:%S')
                    timezone = pytz.timezone(self._context.get('tz') or 'UTC')
                    datetimes = datetimes.astimezone(timezone)

                    # print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',datetimes.strftime('%H'))
                    hours = str(datetimes.strftime('%Y-%m-%d %H:%M:%S'))

                    # date_check = self.env['cube.aging.line'].sudo().search([('datetime', '=', datetime_val)])
                    # if not date_check:
                    date_vals = {
                        'aging_id': self.id,
                        'date': datetime_val,
                        'datetime': datetime_val,
                        'hours': hours,
                        # 'inv_amount': 0,
                        # 'balance': amount,
                    }
                    self.env['cube.aging.line'].sudo().create(date_vals)

                    # date_ar_vals = {
                        #     'ar_id': self.id,
                        #     'date': datetime_val,
                        #     'datetime': datetime_val,
                        #     'inv_amount': 0,
                        #     'balance': amount,
                        # }

                        # aging_ar = self.env['cube.aging.ar'].sudo().create(date_ar_vals)

    def populate_aging(self):
        # get latest datetime
        from_datetime = self.env['cube.aging.balance'].sudo().search([], order='datetime desc', limit=1).datetime
        from_transdatetime = self.env['cube.aging.balance'].sudo().search([], order='trans_createdate desc', limit=1).datetime
        from_datetime = from_transdatetime > from_datetime and from_transdatetime or from_datetime
        to_datetime = datetime.datetime.strptime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
        timezone = pytz.timezone(self._context.get('tz') or 'UTC')
        to_datetime = to_datetime.astimezone(timezone).strftime('%Y-%m-%d %H:%M:%S')
        companies = self.env['dwh.trans'].sudo().search([('create_date', '>=', from_datetime),
                                                         ('create_date', '<', to_datetime)]).read_group(
                                                                        domain=[],
                                                                        fields=['analytic_account_id'],
                                                                        groupby=['analytic_account_id'],
                                                                    )
        # companies = self.env['dwh.trans'].sudo().search([('date_invoice', '<', self.date_to)]).read_group(
        #                                                                 domain=[],
        #                                                                 fields=['analytic_account_id'],
        #                                                                 groupby=['analytic_account_id'],
        #                                                             )
        for comp in companies:
            partner_types = self.env['dwh.trans'].sudo().search([('create_date', '>=', from_datetime),
                                                                 ('create_date', '<', to_datetime),
                                                                 ('analytic_account_id', '=', comp['analytic_account_id'][0])]).read_group(
                                                                        domain=[],
                                                                        fields=['partner_type'],
                                                                        groupby=['partner_type'],
                                                                    )
            # partner_types = self.env['dwh.trans'].sudo().search([('date_invoice', '<', self.date_to), ('analytic_account_id', '=', comp['analytic_account_id'][0])]).read_group(
            #                                                             domain=[],
            #                                                             fields=['partner_type'],
            #                                                             groupby=['partner_type'],
            #                                                         )
            for type in partner_types:
                schedules = self.env['cube.aging.line'].search([('datetime', '>=', from_datetime),
                                                                ('datetime', '<', to_datetime),
                                                                ('aging_id', '=', self.id)], order='datetime asc')
                d0 = False
                balance = 0
                balance_no = 0
                for sch in schedules:
                    d1 = datetime.datetime.strptime(sch.datetime, '%Y-%m-%d %H:%M:%S')
                    d1 += timedelta(hours=1)
                    if d0:
                        dwh = self.env['dwh.trans'].sudo().search([('analytic_account_id', '=', comp['analytic_account_id'][0]),
                                                                   ('partner_type', '=', type['partner_type']),
                                                                   ('create_date', '>=', d0.strftime('%Y-%m-%d %H:%M:%S')),
                                                                   ('create_date', '<', d1.strftime('%Y-%m-%d %H:%M:%S'))])
                        # dwh = self.env['dwh.trans'].sudo().search([('analytic_account_id', '=', comp['analytic_account_id'][0]),
                        #                                            ('partner_type', '=', type['partner_type']),
                        #                                            ('datetime_invoice', '>=', d0.strftime('%Y-%m-%d %H:%M:%S')),
                        #                                            ('datetime_invoice', '<', d1.strftime('%Y-%m-%d %H:%M:%S'))])
                    else:
                        dwh = self.env['dwh.trans'].sudo().search([('analytic_account_id', '=', comp['analytic_account_id'][0]),
                                                                   ('partner_type', '=', type['partner_type']),
                                                                   ('create_date', '>=', from_datetime),
                                                                   ('create_date', '<', d1.strftime('%Y-%m-%d %H:%M:%S'))])
                        # dwh = self.env['dwh.trans'].sudo().search([('analytic_account_id', '=', comp['analytic_account_id'][0]),
                        #                                            ('partner_type', '=', type['partner_type']),
                        #                                            ('datetime_invoice', '<', d1.strftime('%Y-%m-%d %H:%M:%S'))])
                    # dwh = self.env['dwh.trans'].sudo().search([('date_invoice', '<', self.date_to)], order='datetime_invoice asc')
                    d0 = d1
                    if dwh:
                        for row in dwh:
                            invoice_no = row.invoice_no
                            inv_amount = row.inv_amount
                            pay_amount = row.pay_amount
                            # sch = self.env['cube.aging.line'].sudo().search([('analytic_account_id', '=', row.analytic_account_id.id),
                            #                                                  ('type', '=', row.type in ('cust_inv', 'cust_pay') and 'cust_aging' or 'vend_aging')],
                            #                                                 order="datetime asc", limit=1)
                            # if not sch:
                            #     sch = self.env['cube.aging.line'].search([('aging_id', '=', self.id), ('datetime', '<', row.datetime_invoice)], order='datetime asc', limit=1)
                            # if not sch:
                            #     sch = self.env['cube.aging.line'].search([('aging_id', '=', self.id)], order='datetime asc', limit=1)
                            # # bal = self.env['aging.balance.temp'].get_balance(row.analytic_account_id.name,
                            # #                                                  dwh.type in ('cust_inv', 'cust_pay') and 'cust_aging' or 'vend_aging',
                            # #                                                  float(pay_amount) - float(inv_amount))
                            # if sch:
                            balance = balance + float(inv_amount) - float(pay_amount)
                            balance_no += 1
                            date_dwh_vals = {
                                'aging_id': self.id,
                                'balance_no': balance_no,
                                'analytic_account_id': comp['analytic_account_id'][0], #row.analytic_account_id.id,
                                'type': type['partner_type'] == 'Customer' and 'cust_aging' or 'vend_aging',
                                'invoice_no': invoice_no,
                                'date': row.datetime_invoice,
                                'datetime': row.datetime_invoice,
                                'hours': sch.hours,
                                'inv_amount': inv_amount,
                                'pay_amount': pay_amount,
                                'balance': balance,
                            }
                            # print('dwhtttttttttttttttttttttttttt',row.datetime_invoice,datetime_val,amount)
                            aging_dwh = self.env['cube.aging.balance'].sudo().create(date_dwh_vals)
                    else:
                        balance_no += 1
                        date_dwh_vals = {
                            'aging_id': self.id,
                            'balance_no': balance_no,
                            'analytic_account_id': comp['analytic_account_id'][0],
                            'type': type['partner_type'] == 'Customer' and 'cust_aging' or 'vend_aging',
                            'date': sch.date,
                            'datetime': sch.datetime,
                            'hours': sch.hours,
                            'balance': balance,
                        }
                        aging_dwh = self.env['cube.aging.balance'].sudo().create(date_dwh_vals)

    @api.one
    def generate_aging(self):
        # bulan = self.days_cur_month()
        self.populate_schedule()
        self.populate_aging()


class CubeAgingLine(models.Model):
    _name = 'cube.aging.line'
    _description = "Cube Aging Line"
    _rec_name = 'date'
    _order = 'date,datetime asc'

    aging_id = fields.Many2one('cube.aging', string='Aging' ,ondelete='cascade')
    # analytic_account_id = fields.Many2one('account.analytic.account',string="Company")
    # type = fields.Selection([('cust_aging', 'Customer Aging'), ('vend_aging', 'Vendor Aging')], string='Aging Type')
    # invoice_no = fields.Char('Invoice Number')
    date = fields.Date('Date')
    datetime = fields.Datetime('Datetime')
    hours = fields.Char('Datetime')
    # inv_amount = fields.Float('Invoice Amount')
    # pay_amount = fields.Float('Payment Amount')
    # balance = fields.Float('Balance')


class CubeAgingBalance(models.Model):
    _name = 'cube.aging.balance'
    _description = "Cube Aging Balance"
    _rec_name = 'date'
    _order = 'analytic_account_id, type, balance_no, datetime asc'

    aging_id = fields.Many2one('cube.aging', string='Aging' ,ondelete='cascade')
    balance_no = fields.Integer('Balance No.')
    analytic_account_id = fields.Many2one('account.analytic.account',string="Company")
    type = fields.Selection([('cust_aging', 'Customer Aging'), ('vend_aging', 'Vendor Aging')], string='Aging Type')
    invoice_no = fields.Char('Invoice Number')
    trans_date = fields.Date('Transaction Date')
    trans_createdate = fields.Datetime('Transaction Created')
    date = fields.Date('Date')
    datetime = fields.Datetime('Datetime')
    hours = fields.Char('Datetime')
    inv_amount = fields.Float('Invoice Amount')
    pay_amount = fields.Float('Payment Amount')
    balance = fields.Float('Balance')


class CubeAgingAP(models.Model):
    _name = 'cube.aging.ap'
    _description = "Cube Aging A/P"
    _rec_name = 'date'
    _order = 'date,datetime asc'

    ap_id = fields.Many2one('cube.aging', string='AP' ,ondelete='cascade')
    invoice_no = fields.Char('Invoice Number')
    date = fields.Date('Date')
    datetime = fields.Datetime('Datetime')
    hours = fields.Char('Datetime')
    inv_amount = fields.Float('Invoice Amount')
    pay_amount = fields.Float('Payment Amount')
    balance = fields.Float('Balance')

    # @api.model
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     # if 'pin' in groupby or 'pin' in self.env.context.get('group_by', '') or self.env.context.get('no_group_by'):
    #     #     raise exceptions.UserError(_('Such grouping is not allowed.'))
    #     if 'balance' in fields:
    #         fields.remove('balance')

    #     return super(CubeAgingAP, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)


class CubeAgingAR(models.Model):
    _name = 'cube.aging.ar'
    _description = "Cube Aging A/R"
    _rec_name = 'date'
    _order = 'date,datetime asc'

    ar_id = fields.Many2one('cube.aging', string='AR' ,ondelete='cascade')
    invoice_no = fields.Char('Invoice Number')
    date = fields.Date('Date')
    datetime = fields.Datetime('Datetime')
    inv_amount = fields.Float('Invoice Amount')
    pay_amount = fields.Float('Payment Amount')
    balance = fields.Float('Balance')
