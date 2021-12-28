# -*- coding: utf-8 -*-
##############################################################################
#
#    TBD ERP
#    Copyright (C) 2020 TBD ERP
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError
# from datetime import date, timedelta, datetime
import datetime

class DataWarehouse(models.Model):
    _name = 'dwh.trans'
    _description = "Data Transaction A/R A/P Bank"

    invoice_no = fields.Char('Invoice Number')
    partner_name = fields.Char('Partner Name')
    npwp = fields.Char(string='NPWP')
    date_invoice = fields.Date('Invoice Date')
    date_due = fields.Date('Due Date')
    sub_amount = fields.Float('Subtotal Amount')
    ppn_amount = fields.Float('PPN Amount')
    inv_amount = fields.Float('Invoice Amount')
    description = fields.Char()
    po_no = fields.Char('PO Number')
    faktur_no = fields.Char('Tax Number')
    faktur_date = fields.Date('Tax Date')
    payment_no = fields.Char('Payment Number')
    date_payment = fields.Date('Payment Date')
    payment_bank = fields.Char('Bank')
    pph_id = fields.Char('PPH')
    pph_amount = fields.Float('PPH Amount')
    pay_amount = fields.Float('Payment Amount')
    bal_amount = fields.Float('Balance Amount', compute='_get_balance', store=True)
    type = fields.Selection([('cust_inv', 'Customer Invoice'), ('vend_inv', 'Vendor Invoice'), ('cust_pay', 'Customer Payment'), ('vend_pay', 'Vendor Payment'), ('petty_cash', 'Petty Cash Transaction')], string='Document Type')
    partner_type = fields.Char('Partner Type', compute='_get_partner_type', store=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Company")
    datetime_invoice = fields.Datetime('Transaction Date', compute='_get_datetime_invoice', store=True)

    @api.multi
    @api.depends('invoice_no')
    def _get_datetime_invoice(self):
        for line in self:
            d1 = line.date_invoice and line.date_invoice or line.date_payment
            d1 = datetime.datetime.strptime(d1, '%Y-%m-%d')
            d1 = d1.strftime("%Y-%m-%d")

            d2 = line.create_date
            d2 = datetime.datetime.strptime(d2, '%Y-%m-%d %H:%M:%S')
            d2 = d2.strftime("%H:%M:%S")
            datetime_invoice = d1 +' '+ d2
            line.datetime_invoice = datetime_invoice

    _sql_constraints = [
        ('field_unique',
         'unique(analytic_account_id, invoice_no, payment_no)',
         'Choose another value - it has to be unique!')
    ]

    @api.multi
    @api.depends('inv_amount','pph_amount','pay_amount')
    def _get_balance(self):
        for line in self:
            line.bal_amount = line.inv_amount - line.pph_amount - line.pay_amount

    @api.multi
    @api.depends('type')
    def _get_partner_type(self):
        for line in self:
            line.partner_type = line.type in ('cust_inv', 'cust_pay') and 'Customer' or (line.type in ('vend_inv', 'vend_pay') and 'Vendor' or '')
