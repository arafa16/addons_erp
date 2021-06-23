from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError


class BudgetRequestReport(models.TransientModel):
    _name = "sale.invoice.payment.report"
    _order = 'date_invoice, invoice_id'

    invoice_id = fields.Many2one('account.invoice', 'Invoice Id')
    invoice_no = fields.Char('Invoice No')
    reference = fields.Char('Reference')
    date_invoice = fields.Date('Invoice Date')
    date_due = fields.Date('Due Date')
    partner_id = fields.Many2one('res.partner', string='Partner')
    sale_id = fields.Many2one('sale.order', 'Sales No')
    amount_untaxed = fields.Float('DPP') #, currency_field='currency_id')
    amount_tax = fields.Float('Tax') #, currency_field='currency_id')
    amount_total = fields.Float('Total') #, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')

    cost_center_id = fields.Many2one("cost.center", string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    accounts = fields.Char('Account')

    description = fields.Char('Description')

    payment_id = fields.Many2one('payment.journal', 'Payment No')
    payment_date = fields.Date('Payment Date')
    payment_currency_id = fields.Many2one('res.currency', string='Payment Currency')
    move_id = fields.Many2one('account.move', 'Journal No')
    pph_amount = fields.Float('PPH Amount') #, currency_field='payment_currency_id')
    payment_amount = fields.Float('Payment Amount') #, currency_field='payment_currency_id')

    faktur_number = fields.Char(string='Faktur Number')
    faktur_date = fields.Date(string='Faktur Date')
    sales_person = fields.Many2one('res.users', 'Sales Person')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # print('View_id: %s, view_type: %s'%(view_id, view_type))
        res = super(BudgetRequestReport, self).fields_view_get(view_id, view_type, toolbar, submenu)
        if view_type == 'tree':
            # arch = etree.XML(res['arch'])
            # button = arch.xpath("//button[@name='action_budget_to_adjust']")[0]
            # button.set('invisible', self.env.context.get('budget_position') and '0' or '1')
            # setup_modifiers(button)
            # res['arch'] = etree.tostring(arch, encoding='utf-8')
            self.populate_budget_request()
        return res

    @api.multi
    def populate_budget_request(self):
        query = """
            delete from sale_invoice_payment_report;
            select id,
                   number,
                   reference,
                   date_invoice,
                   date_due,
                   partner_id,
                   origin,
                   amount_untaxed,
                   amount_tax,
                   amount_total,
                   currency_id,
                   (select cost_center_id
                    from account_invoice_line
                    where invoice_id = account_invoice.id limit 1) as cost_center_id,
                   (select account_analytic_id
                    from account_invoice_line
                    where invoice_id = account_invoice.id limit 1) as analytic_account_id,
                   name,
                   "FakturNumber",
                   "FakturDate",
                   user_id
            from account_invoice
            where state in ('open', 'paid')
              and type in ('out_invoice', 'out_refund')
        """
        cr = self.env.cr
        # params = (self.env.user.id,) # where create_uid = %s
        cr.execute(query) #, params)
        res = cr.fetchall()

        for r in res:
            line = self.env['sale.invoice.payment.report']
            sale_id = False
            if r[6]:
                sale_id = self.env['sale.order'].sudo().search([('name', '=', r[6])]).id
            query = """
                select concat(code, ':', name) as accounts 
                from account_account where id in (
                    select distinct account_id 
                    from account_invoice_line 
                    where invoice_id = %s
                )
            """
            params = (r[0],)
            cr.execute(query, params)
            accounts = cr.fetchall()

            query = """
                select pj.id, pj.payment_date, pj.move_id, pjl.payment_currency_id, pjl.tax_amt, pjl.total_amt
                from payment_journal_line pjl
                     inner join payment_journal pj on pjl.payment_id = pj.id
                where pj.state = 'posted' and pjl.invoice_id = %s
            """
            params = (r[0],)
            cr.execute(query, params)
            payments = cr.fetchall()
            if payments:
                for pay in payments:
                    line.create({
                        'invoice_id': r[0],
                        'invoice_no': r[1],
                        'reference': r[2],
                        'date_invoice': r[3],
                        'date_due': r[4],
                        'partner_id': r[5],
                        'sale_id': sale_id,
                        'amount_untaxed': r[7],
                        'amount_tax': r[8],
                        'amount_total': r[9],
                        'currency_id': r[10],
                        'cost_center_id': r[11] and r[11] or False,
                        'analytic_account_id': r[12] and r[12] or False,
                        'accounts': ', '.join(x[0] for x in accounts),
                        'description': r[13],
                        'faktur_number': r[14],
                        'faktur_date': r[15],
                        'sales_person': r[16],
                        'payment_id': pay[0],
                        'payment_date': pay[1],
                        'move_id': pay[2],
                        'payment_currency_id': pay[3],
                        'pph_amount': pay[4],
                        'payment_amount': pay[5]
                    })
            else:
                line.create({
                    'invoice_id': r[0],
                    'invoice_no': r[1],
                    'reference': r[2],
                    'date_invoice': r[3],
                    'date_due': r[4],
                    'partner_id': r[5],
                    'sale_id': sale_id,
                    'amount_untaxed': r[7],
                    'amount_tax': r[8],
                    'amount_total': r[9],
                    'currency_id': r[10],
                    'cost_center_id': r[11] and r[11] or False,
                    'analytic_account_id': r[12] and r[12] or False,
                    'accounts': ', '.join(x[0] for x in accounts),
                    'description': r[13],
                    'faktur_number': r[14],
                    'faktur_date': r[15],
                    'sales_person': r[16],
                })