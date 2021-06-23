from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset',
        readonly=False, ondelete='restrict',
        copy=False, index=True, auto_join=True, domain="[('state','in',['open','close'])]")
    date_invoice = fields.Date(
        related='invoice_id.date_invoice', readonly=True, store=True)
    asset_book_value = fields.Float(compute='_get_book_value', method=True, digits=0, string='Book Value')

    @api.multi
    def _get_book_value(self):
        for line in self:
            line.asset_book_value = line.asset_id .value_residual

    @api.onchange('asset_id')
    def onchange_asset_id(self):
        self.asset_category_id = self.asset_id.category_id
        self.account_id = self.asset_category_id.account_asset_id.id
        self.name = self.asset_id.name
        self.cost_center_id = self.asset_id.cost_center_id.id
        self.account_analytic_id = self.asset_id.analytic_account_id.id
        self._get_book_value()

    @api.one
    @api.depends('asset_category_id', 'invoice_id.date_invoice')
    def _get_asset_date(self):
        self.asset_mrr = 0
        self.asset_start_date = False
        self.asset_end_date = False
        cat = self.asset_category_id
        if cat:
            # if cat.method_number == 0 or cat.method_period == 0:
            #     raise UserError(_('The number of depreciations or the period length of your asset category cannot be null.'))
            months = cat.method_number * cat.method_period
            if self.invoice_id.type in ['out_invoice', 'out_refund']:
                self.asset_mrr = self.price_subtotal_signed / months
            if self.invoice_id.date_invoice:
                start_date = datetime.strptime(self.invoice_id.date_invoice, DF).replace(day=1)
                end_date = (start_date + relativedelta(months=months, days=-1))
                self.asset_start_date = start_date.strftime(DF)
                self.asset_end_date = end_date.strftime(DF)

    @api.one
    def asset_create(self):
        if self.asset_category_id:
            if self.asset_id.id == False:
                date_invoice = datetime.strptime(self.invoice_id.date_invoice, DF).date()
                date = date_invoice.day <= 15 and date_invoice.replace(day=1) or date_invoice.replace(day=1) + relativedelta(months=1)
                vals = {
                    'name': self.name,
                    'code': self.invoice_id.number or False,
                    'category_id': self.asset_category_id.id,
                    'value': self.price_subtotal_signed,
                    'partner_id': self.invoice_id.partner_id.id,
                    'company_id': self.invoice_id.company_id.id,
                    'currency_id': self.invoice_id.company_currency_id.id,
                    'date_acq': self.invoice_id.date_invoice,
                    'date': date,
                    'invoice_id': self.invoice_id.id,
                }
                if 'cost_center_id' in self:
                    vals['cost_center_id'] = self.cost_center_id.id
                if 'account_analytic_id' in self:
                    vals['analytic_account_id'] = self.account_analytic_id.id
                changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
                vals.update(changed_vals['value'])
                asset = self.env['account.asset.asset'].create(vals)
                if self.asset_category_id.open_asset:
                    asset.validate()
            else:
                amount = self.asset_id.value + self.price_subtotal_signed
                self.asset_id.write({'value': amount})
        return True
