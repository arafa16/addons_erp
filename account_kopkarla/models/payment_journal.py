# import math
from odoo import api, fields, models, _
from odoo.tools import float_round, float_compare
# from odoo.tools import amount_to_text_en, float_round, float_compare
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero
import logging

INV_TO_PARTN = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}

INV_TO_PAYM_SIGN = {
    'out_invoice': 1,
    'in_refund': 1,
    'in_invoice': -1,
    'out_refund': -1,
}

_logger = logging.getLogger(__name__)


class PaymentJournal(models.Model):
    _name = "payment.journal"
    _order = 'payment_date desc, name desc'

    @api.one
    @api.depends('pph_adjustment_ids')
    def _get_has_pph_adjustment(self):
        self.has_pph_adjustment = bool(self.pph_adjustment_ids)

    name = fields.Char(readonly=True, copy=False) # The name is attributed upon post()
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True, store=True)
    partner_type = fields.Selection([('customer', 'Customer'), ('supplier', 'Vendor')])
    partner_id = fields.Many2one('res.partner', string='Partner')
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type', required=True)
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method Type', required=True)
    hide_payment_method = fields.Boolean(compute='_compute_hide_payment_method',
                          help="Technical field used to hide the payment method if the selected journal has only one available which is 'manual'")
    is_advance_payment = fields.Boolean()
    communication = fields.Char(string='Description')
    amount = fields.Monetary(string='Payment Amount', compute='_calculate_total_payment', readonly=True)
    amount_plan = fields.Monetary(string='Received Amount')
    balance_to_settle = fields.Monetary(string='Payment Amount', compute='_calculate_total_payment', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True, store=True)
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    line_ids = fields.One2many('payment.journal.line', 'payment_id', 'Invoices')
    payment_invoice_id = fields.Many2one('account.payment', string='Account Payment', ondelete="set null", readonly=True)
    move_id = fields.Many2one('account.move', ondelete='set null', string='Journal Entry', store=True, readonly=True)
    pph_adjustment_ids = fields.One2many('payment.journal.line.tax.adjust', 'payment_id', string="PPH Adjustment", copy=False, readonly=True)
    has_pph_adjustment = fields.Boolean(compute="_get_has_pph_adjustment")

    payment_difference = fields.Monetary(compute='_compute_payment_difference', readonly=True)
    # payment_difference_handling = fields.Selection([('open', 'Keep open'), ('reconcile', 'Mark invoice as fully paid')], default='open', string="Payment Difference", copy=False)
    # writeoff_journal_id = fields.Many2one('account.journal', string='Payment Journal', domain=[('type', 'in', ('bank', 'cash'))])
    writeoff_account_id = fields.Many2one('account.account', string="Difference Account", domain=[('deprecated', '=', False)], copy=False)
    writeoff_label = fields.Char(
        string='Journal Item Label',
        help='Change label of the counterpart that will hold the payment difference',
        default='Write-Off')
    created_sign_by = fields.Many2one('hr.employee', string='Dibuat', default=lambda self: self.env['res.config.settings'].get_values().get('default_created_sign_by'))
    checked_sign_by = fields.Many2one('hr.employee', string='Diperiksa', default=lambda self: self.env['res.config.settings'].get_values().get('default_checked_sign_by'))
    known_sign_by = fields.Many2one('hr.employee', string='Mengetahui', default=lambda self: self.env['res.config.settings'].get_values().get('default_known_sign_by'))
    done_sign_by = fields.Many2one('hr.employee', string='Dilaksanakan', default=lambda self: self.env['res.config.settings'].get_values().get('default_done_sign_by'))
    management_sign_by = fields.Many2one('hr.employee', string='Pengurus', default=lambda self: self.env['res.config.settings'].get_values().get('default_management_sign_by'))

    # @api.one
    # def _get_move_id(self):
    #     if self.payment_invoice_id:
    #         move = self.env['account.move'].search([('name', '=', self.payment_invoice_id.move_name)])
    #         self.move_id = move.id

    @api.multi
    def button_pph_adjustment(self):
        action = {
            'name': _('PPH Adjustment'),
            'view_type': 'form',
            'view_mode': 'tree, form',
            # 'res_id': self.id,
            'res_model': 'payment.journal.line.tax.adjust',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('account_kopkarla.view_payment_journal_line_tax_adjustment_tree').id, 'tree'),
                      (self.env.ref('account_kopkarla.view_payment_journal_line_tax_adjustment_form').id, 'form')],
            # 'context': {'active_id': self.id}
            'domain': [('payment_id', '=', self.id)],
        }

        # action['views'] = [(self.env.ref('account.invoice_supplier_tree').id, 'tree'), (self.env.ref('account.invoice_supplier_form').id, 'form')]
        return action

    def set_writeoff_account(self):
        writeoff_account_id = False
        if self.payment_difference > 0:
            writeoff_account_id = self.env['ir.config_parameter'].sudo().get_param('over_payment_account')
        elif self.payment_difference < 0:
            writeoff_account_id = self.env['ir.config_parameter'].sudo().get_param('under_payment_account')
        self.writeoff_account_id = int(writeoff_account_id)

    @api.one
    @api.depends('line_ids', 'line_ids.variance_amt', 'line_ids.settle_full_invoice', 'amount', 'amount_plan', 'payment_date', 'currency_id')
    def _compute_payment_difference(self):
        if len(self.line_ids) == 0:
            return
        if self.amount_plan:
            self.payment_difference = self.amount_plan - self.amount
        if not self.payment_difference:
            payment_difference = 0
            for line in self.line_ids:
                if line.settle_full_invoice and line.variance_amt:
                    payment_difference += line.variance_amt
            self.payment_difference = -payment_difference
            # self.payment_difference = -sum(self.line_ids.mapped('variance_amt'))

    @api.one
    def paymend_invoice_desc(self):
        desc = ""
        for inv in self.line_ids:
            desc += desc and ", " + inv.invoice_id.name or inv.invoice_id.name
        return "Payment " + desc

    @api.multi
    def action_draft(self):
        if self.filtered(lambda payment: payment.state != 'cancelled'):
            raise UserError(_("Payment must be cancelled in order to reset it to draft."))
        # go from canceled state to draft state
        self.write({'state': 'draft'})

    @api.multi
    @api.depends('payment_type', 'journal_id')
    def _compute_hide_payment_method(self):
        for payment in self:
            if not payment.journal_id:
                payment.hide_payment_method = True
                continue
            journal_payment_methods = payment.payment_type == 'inbound'\
                and payment.journal_id.inbound_payment_method_ids\
                or payment.journal_id.outbound_payment_method_ids
            payment.hide_payment_method = len(journal_payment_methods) == 1 and journal_payment_methods[0].code == 'manual'

    @api.onchange('journal_id')
    def _onchange_journal(self):
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            return {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods.ids)]}}
        return {}

    @api.one
    @api.depends('line_ids.total_amt')
    def _calculate_total_payment(self):
        total = 0
        balance = 0
        for line in self.line_ids:
            total += line.total_amt
            balance += line.paying_amt
        self.amount = total
        self.balance_to_settle = balance

    @api.onchange('partner_id')
    def _onchange_parter(self):
        if not self.partner_id:
            self.line_ids = False
        else:
            if self.partner_id.id != self._origin.partner_id.id:
                self.line_ids = False

            # hierarchi parent belum bisa digunakan
            # partner_ids = [self.partner_id.id]
            # if self.partner_id.child_ids:
            #     partner_ids += self.partner_id.child_ids.ids
            payment_lines = []
            domain = [('state', '=', 'open'),
                      ('partner_id', '=', self.partner_id.id),
                       # ('partner_id', 'in', partner_ids),
                       ]
            if self.partner_type == 'customer':
                domain.append(('type', 'in', ['out_invoice', 'out_refund']))
            else:
                domain.append(('type', 'in', ['in_invoice', 'in_refund']))
            invoices = self.env['account.invoice'].search(domain)
            for invoice in invoices:
                exists = False
                for pay_inv in self.line_ids: # check invoice inside payment journal
                    if pay_inv.invoice_id == invoice:
                        exists = True
                        break
                if not exists: # check invoice outside payment journal
                    for pay_inv in self.line_ids.search([('payment_id', '!=', self._origin.id), ('invoice_id', '=', invoice.id)]):
                        if pay_inv.payment_id.state == 'draft':
                            exists = True
                            break
                if not exists:
                    payment_line = (0, False, {'payment_date': self.payment_date,
                                               'partner_id': invoice.partner_id.id,
                                               'invoice_id': invoice.id,
                                               'balance_amt': invoice.residual_signed,
                                               'balance_amt_company': invoice.residual_company_signed})
                    payment_lines.append(payment_line)
            self.line_ids = payment_lines
            # self.update({'line_ids': payment_lines})

    @api.onchange('journal_id')
    def _onchange_journal(self):
        res = {}
        if self.journal_id:
            self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
            # Set default payment method (we consider the first to be the default one)
            payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            self.payment_method_id = payment_methods and payment_methods[0] or False
            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = self.payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            res = {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods.ids)]}}

        active_ids = self._context.get('active_ids')
        invoices = self.env['account.invoice'].browse(active_ids)
        # self.amount = abs(self._compute_payment_amount(invoices))
        return res

    @api.onchange('partner_type')
    def _onchange_partner_type(self):
        # Set partner_id domain
        if self.partner_type:
            return {'domain': {'partner_id': [(self.partner_type, '=', True)]}}

    def _compute_journal_domain_and_types(self):
        journal_type = ['bank', 'cash']
        domain = []
        # if self.currency_id.is_zero(self.amount) and self.has_invoices:
        #     # In case of payment with 0 amount, allow to select a journal of type 'general' like
        #     # 'Miscellaneous Operations' and set this journal by default.
        #     journal_type = ['general']
        #     self.payment_difference_handling = 'reconcile'
        # else:
        if self.payment_type == 'inbound':
            domain.append(('at_least_one_inbound', '=', True))
        elif self.payment_type == 'outbound':
            domain.append(('at_least_one_outbound', '=', True))
        return {'domain': domain, 'journal_types': set(journal_type)}

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        # if not self.invoice_ids:
            # Set default partner type for the payment type
        if self.payment_type == 'inbound':
            self.partner_type = 'customer'
        elif self.payment_type == 'outbound':
            self.partner_type = 'supplier'
        else:
            self.partner_type = False
        # Set payment method domain
        res = self._onchange_journal()
        if not res.get('domain', {}):
            res['domain'] = {}
        jrnl_filters = self._compute_journal_domain_and_types()
        journal_types = jrnl_filters['journal_types']
        journal_types.update(['bank', 'cash'])
        res['domain']['journal_id'] = jrnl_filters['domain'] + [('type', 'in', list(journal_types))]
        return res

    @api.model
    def create(self, vals):
        seq = self.env['ir.sequence'].next_by_code('payment.journal')
        vals['name'] = seq
        res = super(PaymentJournal, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(PaymentJournal, self).write(vals)
        return res

    @api.multi
    def _groupby_invoices(self):
        results = {}
        for line in self.line_ids:
            inv = line.invoice_id
            # key = (inv.commercial_partner_id.id, INV_TO_PARTN[inv.type])
            key = (inv.partner_id.id, INV_TO_PARTN[inv.type])
            if not key in results:
                results[key] = self.env['account.invoice']
            results[key] += inv
        return results

    @api.multi
    def _prepare_payment_vals(self, invoices):
        if self.amount_plan:
            payment_amt = self.amount_plan
        else:
            payment_amt = self.amount
        payment_amt += sum(self.line_ids.mapped('tax_amt'))
        if self.payment_difference < 0:
            payment_amt += abs(self.payment_difference)
        # amount = self._compute_payment_amount(invoices) if self.multi else self.amount
        # balance_to_settle = self.balance_to_settle
        # payment_type = ('inbound' if amount > 0 else 'outbound') if self.multi else self.payment_type
        payment_type = self.payment_type
        val = {
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'payment_date': self.payment_date,
            'communication': self.name, # self.communication,  # DO NOT FORWARD PORT TO V12 OR ABOVE
            'invoice_ids': [(6, 0, invoices.ids)],
            'payment_line_ids': [(6, 0, self.line_ids.ids)],
            'payment_type': payment_type,
            # 'amount': abs(balance_to_settle),
            'amount': abs(payment_amt),
            'currency_id': self.currency_id.id,
            'partner_id': invoices[0].commercial_partner_id.id,
            'partner_type': INV_TO_PARTN[invoices[0].type],
        }
        if self.payment_difference:
            val.update({'payment_difference_handling': 'reconcile',
                        # 'payment_difference': self.payment_difference, # calculate by compute
                        'writeoff_account_id': self.writeoff_account_id.id,
                        'writeoff_label': self.writeoff_label})

        return val

    @api.multi
    def get_payments_vals(self):
        groups = self._groupby_invoices()
        return [self._prepare_payment_vals(invoices) for invoices in groups.values()]

    def _validate_payment(self):
        if not self.line_ids:
            raise UserError(_("Select invoice to paid."))

        for line in self.line_ids:
            if line.paying_amt > 0:
                for tax in line.tax_line_ids:
                    if tax.mandatory_faktur:
                        if not tax.tax_no or not tax.tax_date:
                            raise UserError(_("Faktur number and faktur date is mandatory."))
            elif line.paying_amt == 0:
                line.unlink()

        # if self.amount_plan and self.amount != self.amount_plan:
        #     raise ValidationError(_('Payment amount and received amount are different!'))

    def post(self):
        self._validate_payment()
        Payment = self.env['account.payment']
        payments = Payment
        payment_vals = self.get_payments_vals()
        for payment_val in payment_vals:
            payments += Payment.create(payment_val)
        for pay in payments:
            pay.post_payment_journal(self)
            move = self.env['account.move'].search([('name', '=', pay.move_name)])
            _logger.warning("Payment: %s, Move: %s" % (pay.communication, move.mapped('name')))
            for line in move.line_ids:
                line.name = '%s: %s' % (self.name, self.communication)
            self.write({'payment_invoice_id': pay.id, 'move_id': move.id, 'state': 'posted'})
        return True

    @api.multi
    def unlink(self):
        for pay in self:
            if pay.state not in ('draft', 'cancelled'):
                raise UserError(_('You can not delete a document not in draft or cancel state! Try to cancel it before.'))
        return super(PaymentJournal, self).unlink()


class PaymentJournalLine(models.Model):
    _name = "payment.journal.line"
    _rec_name = 'invoice_id'

    def _update_amount(self):
        tax_amt = 0
        for tax_id in self.tax_ids.ids:
            payment = self.payment_id
            for inv in payment.line_ids:
                if inv.invoice_id == self.invoice_id:
                    payment_invoice_id = inv.id
                    break
            tax_line = self.tax_line_ids.search([('payment_invoice_id', '=', payment_invoice_id), ('tax_id', '=', tax_id)])
            if not tax_line:
                tax_amt += self.get_tax(inv.invoice_id.amount_untaxed_signed, tax_id)['tax_amt'] # (self.paying_amt, tax_id)['tax_amt'] hp
            else:
                tax_amt += tax_line.set_tax(self.invoice_id.amount_untaxed_signed) # (self.paying_amt) hp

        #     tax_amt += tax_line.tax_amt
        if not tax_amt:
            for tax_line in self.tax_line_ids:
                tax_amt += tax_line.tax_amt
        self.tax_amt = round(tax_amt)
        total_amt = self.paying_amt - self.tax_amt
        self.total_amt = total_amt

    @api.onchange('paying_amt', 'tax_ids', 'tax_line_ids', 'tax_line_ids.tax_amt')
    def _change_paying_amt(self):
        self._check_paying_amt()
        self._update_amount()
        self._calculate_variance()

    def get_tax(self, base_amt, tax_id):
        account_tax = self.env['account.tax'].search([('id', '=', tax_id)])
        return {'account_id': account_tax.account_id.id, 'tax_pct': account_tax.amount,
                'tax_amt': account_tax.amount_type == 'percent' and (base_amt * account_tax.amount / 100)}

    payment_id = fields.Many2one('payment.journal', string="Invoices", required=True, ondelete='cascade', index=True)
    invoice_id = fields.Many2one('account.invoice', string="Invoice", required=True)
    date_invoice = fields.Date(string='Invoice Date', compute='_set_invoice_date')
    date_due = fields.Date(string='Due Date', compute='_set_invoice_date')
    payment_invoice_id = fields.Many2one('account.payment', string='Account Payment', ondelete="set null", readonly=True)
    payment_date = fields.Date(string='Payment Date', related="payment_id.payment_date", required=True, copy=False, store=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id', store=True, related_sudo=False)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True, store=True)
    payment_currency_id = fields.Many2one('res.currency', related='payment_id.currency_id', string="Payment Currency", readonly=True, store=True)

    balance_amt = fields.Monetary("Balance Amt", required=True, currency_field='currency_id')
    balance_amt_company = fields.Monetary("Balance Amt Base Currency", currency_field='company_currency_id') # required=True,
    paying_amt = fields.Monetary("Balance to Pay", digits=(16, 2), currency_field='payment_currency_id')
    variance_amt = fields.Monetary("Variance", digits=(16, 2), compute='_calculate_variance', currency_field='payment_currency_id')
    # tax_amt = fields.Monetary(string='WHT Amount', readonly=True, compute='_compute_amount')
    tax_amt = fields.Monetary(string='WHT Amount', readonly=True, store=True, currency_field='payment_currency_id') #, compute='_compute_amount')
    total_amt = fields.Monetary("Paid Amount", store=True, readonly=True, currency_field='payment_currency_id')
    tax_line_ids = fields.One2many('payment.journal.line.tax', 'payment_invoice_id', string='Tax Lines')
    tax_ids = fields.Many2many('account.tax', 'payment_journal_line_tax_rel', 'payment_invoice_id', 'tax_id', string='WHT',
                               domain=lambda self: self._domain_tax_ids())
    # move_id = fields.Many2one('account.move', compute='_get_move_id', ondelete='restrict', method=True, string='Journal Entry')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('sent', 'Sent'), ('reconciled', 'Reconciled'), ('cancelled', 'Cancelled')],
                             related='payment_id.state', readonly=True, copy=False, string="Status")
    settle_full_invoice = fields.Boolean(string='Close')

    def _calculate_variance(self):
        for pay in self:
            pay.variance_amt = pay.balance_amt - pay.paying_amt

    @api.one
    @api.depends('invoice_id')
    def _set_invoice_date(self):
        self.date_invoice = self.invoice_id.date_invoice
        self.date_due = self.invoice_id.date_due

    # @api.one
    # def _get_move_id(self):
    #     if self.payment_invoice_id:
    #         move = self.env['account.move'].search([('name', '=', self.payment_invoice_id.move_name)])
    #         self.move_id = move.id

    @api.multi
    def full_avail_pay(self):
        available = abs(self.payment_id.amount - self.payment_id.amount_plan)
        if self.payment_id.amount_plan and not available:
            raise ValidationError(_('Available plan amount has been reserved!'))
        # available = (self.payment_id.amount_plan > 0 and self.payment_id.amount_plan or self.balance_amt) - self.payment_id.amount
        self.recursive_set_pay_amt(self.balance_amt) #, available)
        self.payment_id.set_writeoff_account()

    @api.multi
    def show_tax_line(self):
        tax_line_view = self.env.ref('account_kopkarla.view_payment_journal_line_tax')
        return {
            'name': _('Taxes Line'),
            'res_model': 'payment.journal.line',
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            # 'view_type': 'tree,form',
            # 'view_mode': 'form',
            # 'view_id': tax_line_view.id,
            'views': [(tax_line_view.id, 'form')],
            'target': 'current',
            # 'domain': [('payment_invoice_id', '=', self.id)],
            # 'context': self.env.context,
        }

    def recursive_set_pay_amt(self, pay_amount, stop = False): # available):
        # available -= self.paying_amt
        self.paying_amt = round(pay_amount, 2) # - self.paying_amt < available and self.balance_amt or available
        self._change_paying_amt()
        if stop or self.payment_id.amount_plan == 0:
            if not self.payment_id.amount_plan == 0:
                available = round(self.payment_id.amount_plan - self.payment_id.amount, 2)
                i = 0
                while self.payment_id.amount_plan != self.payment_id.amount and i < 5:
                    i += 1
                    available *= i
                    self.paying_amt = round(pay_amount + available, 2)
                    self._change_paying_amt()
            return
        # if pay_amount > available:
        available = round(self.payment_id.amount_plan - self.payment_id.amount, 2)
        # available = round(self.payment_id.amount_plan > 0 and (self.payment_id.amount_plan - self.payment_id.amount) or (self.balance_amt - self.paying_amt), 2)
        if self.paying_amt != self.balance_amt or available < 0:
            if abs(available) <= self.currency_id.rounding or available > 0:
                stop = True
            if self.payment_id.amount != self.payment_id.amount_plan or self.paying_amt != self.balance_amt:
                self.recursive_set_pay_amt(round(self.paying_amt + available / 2, 2), stop) #, available)

    @api.constrains('paying_amt')
    def _check_paying_amt(self):
        if self.paying_amt > self.balance_amt:
            self.paying_amt = self.balance_amt

    @api.depends('invoice_id')
    def _domain_tax_ids(self):
        return [
           ('active', '=', True),
           # ('type_tax_use', '=', 'purchase'),
       ]

    @api.model
    def create(self, vals):
        tax_lines = []
        untax_amt = self.env['account.invoice'].sudo().browse(vals['invoice_id']).amount_untaxed_signed
        for tax_id in vals['tax_ids'][0][2]:
            tax = self.get_tax(untax_amt, tax_id) # (vals['paying_amt'], tax_id) hp
            tax_lines.append({'payment_id': vals['payment_id'],
                              'tax_id': tax_id,
                              'account_id': tax['account_id'],
                              'base_amt': untax_amt, # vals['paying_amt'], hp
                              'tax_pct': tax['tax_pct'],
                              'tax_amt': tax['tax_amt']})
        vals['tax_line_ids'] = [[0, False, line] for line in tax_lines]
        res = super(PaymentJournalLine, self).create(vals)
        # self._compute_amount()
        return res

    @api.one
    def write(self, vals):
        # paying_amt = 'paying_amt' in vals and vals['paying_amt'] or self.paying_amt hp
        untax_amt = self.invoice_id.amount_untaxed_signed # hp
        if 'tax_ids' in vals:
            tax_lines = []
            for tax_id in vals['tax_ids'][0][2]:
                tax_exist = self.env['payment.journal.line.tax'].search([('payment_invoice_id', '=', self.id), ('tax_id', '=', tax_id)])
                if not tax_exist:
                    tax = self.get_tax(untax_amt, tax_id) # (paying_amt, tax_id) hp
                    tax_lines.append([0, False, {'payment_id': self.payment_id.id, 'tax_id': tax_id, 'account_id': tax['account_id'], 'base_amt': untax_amt, # paying_amt, hp
                                                 'tax_pct': tax['tax_pct'], 'tax_amt': tax['tax_amt']}])
                # else:
                #     tax_lines.append([6, False, {'tax_id': tax_id}])
            vals['tax_line_ids'] = tax_lines

            tax_exist = self.env['payment.journal.line.tax'].search([('payment_invoice_id', '=', self.id)])
            for tax in tax_exist:
                if tax.tax_id.id not in vals['tax_ids'][0][2]:
                    tax.unlink()
                    # tax_lines.append((2, tax.tax_id.id))
        # else:
        #     for tax_line in self.tax_line_ids:
        #         if abs(tax_line.base_amt) > abs(untax_amt): # paying_amt: hp
        #             tax_line.base_amt = untax_amt # paying_amt: hp
        #             tax_line.tax_amt = tax_line.tax_id.amount_type == 'percent' and untax_amt * tax_line.tax_id.amount / 100 # paying_amt * tax_line.tax_id.amount / 100 hp
        res = super(PaymentJournalLine, self).write(vals)
        return res

    @api.multi
    def action_payment_undo(self):
        self.payment_invoice_id.cancel()
        self.payment_invoice_id.unlink()


class AccountInvoiceTax(models.Model):
    _name = "payment.journal.line.tax"
    _rec_name = 'tax_id'

    payment_id = fields.Many2one('payment.journal', string="Payment", required=True, ondelete='cascade', index=True)
    payment_invoice_id = fields.Many2one('payment.journal.line', string='Invoice', ondelete='cascade', index=True)
    tax_id = fields.Many2one('account.tax', string='Tax', readonly=True, ondelete='restrict', domain=[('type_tax_use', '=', 'purchase'), ('tax_group_id', '=', 'WHT')])
    tax_pct = fields.Float("Tax (%)", readonly=True)
    account_id = fields.Many2one('account.account', string='Tax Account', required=True, compute='_get_tax_info', store=True)
    # # account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    currency_id = fields.Many2one('res.currency', related='payment_invoice_id.currency_id', store=True, readonly=True)
    # # base = fields.Monetary(string='Base', compute='_compute_base_amount', store=True)
    paying_amt = fields.Float("Payment Amount", compute='_get_paying_amount')
    base_amt = fields.Float("WHT Base Amount", digits=(16, 2))
    tax_amt = fields.Float("WHT Amount", readonly=True)
    tax_no = fields.Char("Tax Number", copy=False) # The name is attributed upon post()
    tax_date = fields.Date('Tax Date', copy=False)
    mandatory_faktur = fields.Boolean(string="Mandatory Faktur", compute='_get_mandatory_faktur')

    @api.one
    def _get_mandatory_faktur(self):
        res = self.env['res.config.settings'].get_values()
        self.mandatory_faktur = res.get('mandatory_faktur')

    # # amount_rounding = fields.Monetary()
    # amount_total = fields.Monetary(string="Amount", compute='_compute_amount_total')
    # manual = fields.Boolean(default=True)
    # company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)

    # @api.onchange('base_amt')
    # def _change_tax_amount(self):

    @api.one
    def _tax_validate(self):
        # if self.base_amt > self.paying_amt:
        #     raise UserError(_('WHT base amount is not allowed greater than payment amount.'))
        if self.base_amt == 0:
            raise UserError(_('WHT base amount is not allowed to be zero.'))

    @api.depends('tax_id', 'base_amt')
    @api.one
    def _get_tax_info(self):
        # self._tax_validate()
        self.account_id = self.tax_id.account_id.id
        self.tax_pct = self.tax_id.amount
        self.tax_amt = self.base_amt * self.tax_pct / 100

    @api.one
    def _get_paying_amount(self):
        self.paying_amt = self.payment_invoice_id.paying_amt

    def set_tax(self, base_amt):
        if not self.base_amt:
            self.base_amt = base_amt
            self.tax_amt = self.base_amt * self.tax_pct / 100
        return self.tax_amt

    @api.model
    def create(self, vals):
        return super(AccountInvoiceTax, self).create(vals)

    @api.one
    def write(self, vals):
        return super(AccountInvoiceTax, self).write(vals)


class PaymentTaxAdjustmentJournal(models.Model):
    _name = "payment.journal.line.tax.adjust"
    _description = "Payment Journal Line Tax Adjustment"

    name = fields.Char('Adjustment Name', required=True, index=True)
    date = fields.Date('Adjustment Date', required=True)
    description = fields.Char(string='Reason', required=True)
    payment_id = fields.Many2one('payment.journal', string="Original Payment", required=True, readonly=True, ondelete='cascade', index=True)
    payment_invoice_id = fields.Many2one('payment.journal.line', string='Original Invoice', ondelete='cascade', index=True)
    tax_id = fields.Many2one('account.tax', string='Tax', readonly=True, ondelete='restrict')
    currency_id = fields.Many2one('res.currency', readonly=True)
    base_amt = fields.Float("WHT Base Amount", digits=(16, 2), readonly=True)
    tax_pct = fields.Float("Tax (%)", readonly=True)
    tax_amt = fields.Float("WHT Amount", readonly=True)
    tax_no = fields.Char("Tax Number")
    tax_date = fields.Date('Tax Date')
    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted'), ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")
    invoice_id = fields.Many2one('account.invoice', string="Invoice", ondelete='set null', readonly=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', ondelete='set null', readonly=True)

    @api.multi
    def _create_invoice(self):
        inv_obj = self.env['account.invoice']
        ir_property_obj = self.env['ir.property']
        # if self.product_id.id:
        #     account_id = order.fiscal_position_id.map_account(self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id).id
        # if not account_id:
        #     inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
        #     account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
        # if not account_id:
        #     raise UserError(
        #         _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
        #         (self.product_id.name,))
        #
        # if self.amount <= 0.00:
        #     raise UserError(_('The value of the down payment amount must be positive.'))
        # context = {'lang': order.partner_id.lang}
        # if self.advance_payment_method == 'percentage':
        #     amount = order.amount_untaxed_signed * self.amount / 100
        #     name = _("Down payment of %s%%") % (self.amount,)
        # else:
        #     amount = self.amount
        #     name = _('Down Payment')
        # del context
        # taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
        # if order.fiscal_position_id and taxes:
        #     tax_ids = order.fiscal_position_id.map_tax(taxes).ids
        # else:
        #     tax_ids = taxes.ids
        invoice = inv_obj.create({
            # 'name': self.payment_id.name,
            'origin': self.payment_id.name,
            'date_invoice': self.date,
            'type': 'in_invoice',
            'reference': False,
            'account_id': self.payment_id.partner_id.property_account_payable_id.id,
            'partner_id': self.payment_id.partner_id.id,
            # 'partner_shipping_id': self.payment_invoice_id.dest_address_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name,
                'origin': self.payment_invoice_id.invoice_id.number,
                'account_id': self.tax_id.refund_account_id.id,
                'price_unit': self.tax_amt,
                'quantity': 1.0,
                # 'discount': 0.0,
                # 'uom_id': self.product_id.uom_id.id,
                # 'product_id': self.product_id.id,
                # 'purchase_line_id': po_line.id,
                # 'invoice_line_tax_ids': [(6, 0, tax_ids)],
                # 'account_analytic_id': order.analytic_account_id.id or False,
            })],
            'currency_id': self.currency_id.id,
            'payment_term_id': self.payment_invoice_id.invoice_id.payment_term_id.id,
            'FakturNumber': self.tax_no,
            'FakturDate': self.tax_date,
            # 'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
            # 'team_id': order.team_id.id,
            'user_id': self.env.user.id,
            'reference': self.payment_id.name,
        })
        invoice.compute_taxes()
        invoice._onchange_payment_term_date_invoice()
        # invoice.message_post_with_view('mail.message_origin_link',
        #             values={'self': invoice, 'origin': order},
        #             subtype_id=self.env.ref('mail.mt_note').id)
        return invoice

    @api.multi
    def action_move_create(self, invoice):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        if not invoice.journal_id.sequence_id:
            raise UserError(('Please define sequence on the journal related to this invoice.'))
        if not invoice.invoice_line_ids:
            raise UserError(('Please create some invoice lines.'))
        # if invoice.move_id:
        #     continue

        # context = dict(self.env.context)
        # Within the context of an invoice asset with the type of the invoice.

        ctx = dict(invoice._context, lang=invoice.partner_id.lang)
        ctx.pop('default_type', None)
        # inv.invoice_line_ids.with_context(ctx).asset_create()

        if not invoice.date_invoice:
            invoice.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
        if not invoice.date_due:
            invoice.with_context(ctx).write({'date_due': invoice.date_invoice})
        company_currency = invoice.company_id.currency_id

        # create move lines (one per invoice line + eventual taxes and analytic lines)
        iml = invoice.invoice_line_move_line_get()
        iml[0].update({
            'tax_line_id': self.tax_id.id,
            'tax_no': self.tax_no,
            'tax_date': self.tax_date,
        })
        # iml += inv.tax_line_move_line_get()

        diff_currency = invoice.currency_id != company_currency
        # create one move line for the total and possibly adjust the other lines amount
        total, total_currency, iml = invoice.with_context(ctx).compute_invoice_totals(company_currency, iml)

        name = invoice.name or '/'
        if invoice.payment_term_id:
            totlines = invoice.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, invoice.date_invoice)[0]
            res_amount_currency = total_currency
            ctx['date'] = invoice._get_currency_rate_date()
            for i, t in enumerate(totlines):
                if invoice.currency_id != company_currency:
                    amount_currency = company_currency.with_context(ctx).compute(t[1], invoice.currency_id)
                else:
                    amount_currency = False

                # last line: add the diff
                res_amount_currency -= amount_currency or 0
                if i + 1 == len(totlines):
                    amount_currency += res_amount_currency

                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': t[1],
                    'account_id': invoice.account_id.id,
                    'date_maturity': t[0],
                    'amount_currency': diff_currency and amount_currency,
                    'currency_id': diff_currency and invoice.currency_id.id,
                    'invoice_id': invoice.id
                })
        else:
            iml.append({
                'type': 'dest',
                'name': name,
                'price': total,
                'account_id': invoice.account_id.id,
                'date_maturity': invoice.date_due,
                'amount_currency': diff_currency and total_currency,
                'currency_id': diff_currency and invoice.currency_id.id,
                'invoice_id': invoice.id
            })
        part = self.env['res.partner']._find_accounting_partner(invoice.partner_id)
        line = [(0, 0, invoice.line_get_convert(l, part.id)) for l in iml]
        line = invoice.group_lines(iml, line)

        journal = invoice.journal_id.with_context(ctx)
        line = invoice.finalize_invoice_move_lines(line)

        date = invoice.date or invoice.date_invoice
        move_vals = {
            'ref': invoice.reference,
            'line_ids': line,
            'journal_id': journal.id,
            'date': date,
            'narration': invoice.comment,
        }
        ctx['company_id'] = invoice.company_id.id
        ctx['invoice'] = invoice
        ctx_nolang = ctx.copy()
        ctx_nolang.pop('lang', None)
        move = account_move.with_context(ctx_nolang).create(move_vals)
        # Pass invoice in context in method post: used if you want to get the same
        # account move reference when creating the same invoice after a cancelled one:
        move.post()

        # make the invoice point to that move
        vals = {
            'move_id': move.id,
            'date': date,
            'move_name': move.name,
        }
        invoice.with_context(ctx).write(vals)
        self.update({
            'invoice_id': invoice.id,
            'move_id': move.id,
            'state': 'posted',
        })
        # for invoice in self:
        #     for line in invoice.invoice_line_ids:
        #         if line.asset_id.id == False:
        #             asset = self.env['account.asset.asset'].sudo().search([('invoice_id', '=', line.invoice_id.id), ('name', '=', line.name)])
        #             for move_line in invoice.move_id.line_ids:
        #                 if (move_line.name == line.name and move_line.user_type_id.name == 'Fixed Assets'):
        #                     move_line.asset_id = asset.id
        #             line.asset_id = asset.id
        #         else:
        #             for move_line in invoice.move_id.line_ids:
        #                 if (move_line.name == line.name and move_line.user_type_id.name == 'Fixed Assets'):
        #                     move_line.asset_id = line.asset_id
            # # Close asset
            # if invoice.journal_type == 'asset_sale':
            #     invoice.invoice_line_asset_sale_closed(move.id, date)

        return True

    @api.multi
    def post(self):
        invoice = self._create_invoice()
        self.action_move_create(invoice)
        return invoice.invoice_validate()
        # if self._context.get('open_invoices', False):
        #     return purchase_orders.action_view_invoice()
        # return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_draft(self):
        if self.filtered(lambda doc: doc.state != 'cancelled'):
            raise UserError(_("Document must be cancelled in order to reset it to draft."))
        # go from canceled state to draft state
        self.write({'state': 'draft'})

    @api.multi
    def action_cancel(self):
        self.invoice_id.action_invoice_cancel()
        self.invoice_id.unlink()
        return self.write({'state': 'cancelled'})

    # @api.multi
    # def action_payment_undo(self):
    #     self.payment_invoice_id.cancel()
    #     self.payment_invoice_id.unlink()
    #     # self.move_id.button_cancel()
    #     # self.move_id.unlink()
