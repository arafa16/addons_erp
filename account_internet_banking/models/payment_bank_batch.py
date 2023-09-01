import base64
import re
import csv
import odoo.tools
import datetime
import math
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from num2words import num2words


class PaymentBankBatch(models.Model):
    _name = "payment.bank.batch"
    _order = 'date desc, name desc'

    name = fields.Char(readonly=True, copy=False, size=32,) # The name is attributed upon post()
    date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True,
                                 states={'post': [('readonly', True)]})
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))],
                                 readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', related='journal_id.bank_account_id.currency_id', readonly=True)
    amount = fields.Monetary(string='Payment Amount', compute='_calculate_total_payment', readonly=True)
    line_ids = fields.One2many('payment.bank.batch.line', 'batch_id', 'Lines')
    state = fields.Selection([('draft', 'Draft'), ('export', 'Exported'), ('post', 'Posted'), ('cancel', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    export_file = fields.Binary(string="Exported File",)
    export_filename = fields.Char(string="Exported File",)
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, store=True)
    text_amount = fields.Char(string="Terbilang", required=False, compute="amount_to_words")
    approver1_id = fields.Many2one('hr.employee', string='Approver 1', default=lambda self: self.env['res.config.settings'].get_values().get('default_batch_payment1_by'))
    approver2_id = fields.Many2one('hr.employee', string='Approver 2', default=lambda self: self.env['res.config.settings'].get_values().get('default_batch_payment2_by'))

    def titlecase(self, s):
        return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), s)

    @api.depends('amount')
    def amount_to_words(self):
        if self.company_id.text_amount_language_currency:
            i_amount_total = int(self.amount)
            if (float(i_amount_total) < self.amount):
                self.text_amount = self.titlecase(num2words(self.amount, to='currency',
                                                            lang=self.company_id.text_amount_language_currency))
            elif (float(i_amount_total) == self.amount):
                self.text_amount = self.titlecase(num2words(i_amount_total, to='currency',
                                                            lang=self.company_id.text_amount_language_currency))

    @api.one
    @api.depends('line_ids.amount')
    def _calculate_total_payment(self):
        self.amount = self.line_ids.read_group(domain=[('batch_id','=',self.id)], fields=['amount'], groupby=[])[0]['amount']

    @api.onchange("journal_id")
    def _onchange_journal_id(self):
        for batch in self:
            line_ids = []
            amount_total = 0
            for payment_id in self.env["payment.journal"].sudo().search([('journal_id','=',batch.journal_id.id),('state','=','confirm')]):
                amount = math.ceil(payment_id.amount)
                desc = re.sub('[`~!@#$%^&*()-+,.<>/?;:\'\"{}|]', ' ',
                              " ".join([i.invoice_id.origin if i.invoice_id.origin else (
                                  i.invoice_id.reference if i.invoice_id.reference else (i.invoice_id.name if i.invoice_id.name else i.invoice_id.number))
                                        for i in payment_id.line_ids])[:32])
                line_ids.append((0, 0, {'payment_id': payment_id.id,
                                        'partner_id': payment_id.partner_id,
                                        'partner_bank_id': payment_id.partner_bank_id,
                                        'currency_id': payment_id.currency_id,
                                        'amount': amount,
                                        'description': desc}))
                amount_total += amount
            batch.line_ids = len(line_ids) and line_ids or False
            batch.amount = amount_total

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('payment.bank.batch')
        result = super(PaymentBankBatch, self).create(vals)
        return result

    @api.multi
    def unlink(self):
        for batch in self:
            if batch.state not in ['draft']:
                raise UserError(_('You cannot delete a document is in %s state.') % (batch.state,))
            for payment in batch.line_ids:
                payment.unlink()
        return super(PaymentBankBatch, self).unlink()

    @api.multi
    def export(self):
        return {
            'name': "Export Batch %s%s" % (self.name, ' Complete' if self.state != 'draft' else ''),
            'type': 'ir.actions.act_window',
            'res_model': 'payment.bank.batch',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('account_internet_banking.view_payment_bank_batch_export_wizard').id,
            'target': 'new',
        }

    @api.multi
    def export_confirm(self):
        batch_line = self.line_ids.read_group(domain=[('batch_id', '=', self.id)], fields=['amount'], groupby=[])
        with open('/tmp/export.csv', mode='w') as file:
            writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            # create a row contains heading of each column
            writer.writerow(['P', datetime.datetime.strptime(self.date, '%Y-%m-%d').strftime('%Y%m%d'), self.journal_id.bank_account_id.acc_number, batch_line[0]['__count'], int(batch_line[0]['amount'])])
            # fetch products and write respective data.
            for line in self.line_ids:
                writer.writerow([line.partner_bank_id.acc_number, line.partner_bank_id.acc_name,
                                 '', '', '',
                                 line.currency_id.name, int(line.amount), line.description[:20],
                                 '',
                                 'LBU' if line.partner_bank_id.bank_id != self.journal_id.bank_id else 'IBU',
                                 line.partner_bank_id.bank_id.bic if line.partner_bank_id.bank_id != self.journal_id.bank_id else '',
                                 line.partner_bank_id.bank_id.name, 'Jakarta',
                                 '', '', '',
                                 # 'Y', line.partner_id.email if line.partner_id.email else 'dwi.istianingsih@kopkarla.co.id',
                                 'Y', 'finance.payment@kopkarla.co.id',
                                 '', '', '', '', '', '', '', '', '', '', '',
                                 '', '', '', '', '', '', '', '', '', '', '', line.description[:20]
                                ])
        # file.close()
        fo = open('/tmp/export.csv', "rb")
        self.export_file = base64.b64encode(fo.read())
        fo.close()
        self.export_filename = '%s - %s - %s.csv' % (self.journal_id.bank_id.name, datetime.datetime.strptime(self.date, '%Y-%m-%d').strftime('%Y%m%d'), self.name) #'export.csv'
        self.state = 'export'
        self.export

    @api.multi
    def post(self):
        for batch in self:
            for payment in batch.line_ids:
                payment.payment_id.payment_date = batch.date
                payment.payment_id.post()
            batch.state = 'post'

    @api.multi
    def action_cancel(self):
        for batch in self:
            if batch.state == 'post':
                for payment in batch.line_ids:
                    payment.payment_id.action_cancel()
                    payment.payment_id.state = 'sent'
            batch.export_file = False
            batch.export_filename = False
            # batch.state = 'cancel'
            batch.state = 'draft'

    @api.multi
    def action_draft(self):
        self.state = 'draft'


class PaymentBankBatchLine(models.Model):
    _name = "payment.bank.batch.line"
    _order = 'payment_id desc'

    batch_id = fields.Many2one('payment.bank.batch', string="Batch", required=True, ondelete="cascade", index=True)
    payment_id = fields.Many2one('payment.journal', string="Payment Journal", required=True, ondelete="restrict", readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, ondelete="restrict", readonly=True)
    partner_bank_id = fields.Many2one('res.partner.bank', string='Bank', domain="[('partner_id', '=', partner_id)]")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    amount = fields.Monetary(string='Amount', required=True, readonly=True)
    description = fields.Char(readonly=True, copy=False, size=32,)

    @api.model
    def create(self, vals):
        self.env["payment.journal"].sudo().browse(vals['payment_id']).update({'state': 'sent'})
        return super(PaymentBankBatchLine, self).create(vals)

    @api.multi
    def unlink(self):
        for payment in self:
            payment.payment_id.state = 'confirm'
        return super(PaymentBankBatchLine, self).unlink()
