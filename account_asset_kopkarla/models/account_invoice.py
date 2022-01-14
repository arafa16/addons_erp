from odoo import api, models, fields
from odoo.exceptions import UserError

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    # journal_type = fields.Char(compute='_get_journal_type', store=True)
    #
    # @api.one
    # @api.depends('journal_id')
    # def _get_journal_type(self):
    #     self.journal_type = self.journal_id.type

    @api.model
    def default_get(self,fields):
        result = super(AccountInvoice, self).default_get(fields)
        journal = self.get_journal()
        if journal:
            result['journal_id'] = journal.id

        return result

    def get_journal(self):
        if self._context.get('default_asset_sale', False):
            asset_sale = self._context.get('default_asset_sale', 'asset_sale')
            company_id = self._context.get('company_id', self.env.user.company_id.id)
            domain = [
                ('type', '=', asset_sale),
                ('company_id', '=', company_id),
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            return journal

    @api.model
    def _default_journal(self):
        self.get_journal()
        return super(AccountInvoice, self)._default_journal()

    def cancel_prev_receiving(self):
        res = []
        for line in self.invoice_line_ids:
            if line.asset_category_id:
                if line.purchase_line_id:
                    stock_move = self.env['stock.move'].sudo().search([('purchase_line_id', '=', line.purchase_line_id.id)])
                    if stock_move.move_id:
                        for move_line in stock_move.move_id.line_ids:
                            move_line_dict = {
                                'name': line.name,
                                'product_id': line.product_id.id,
                                'quantity': line.quantity,
                                'product_uom_id': line.product_id.uom_id.id,
                                'ref': stock_move.picking_id.name,
                                'partner_id': self.partner_id.id,
                                'debit': line.price_subtotal if move_line.debit == 0 else 0,
                                'credit': line.price_subtotal if move_line.credit == 0 else 0,
                                'account_id': move_line.account_id.id,
                                'cost_center_id': line.cost_center_id.id,
                                'analytic_account_id': line.account_analytic_id.id,
                            }
                            res.append((0, 0, move_line_dict))
        return res

    @api.multi
    def action_move_create(self):
        """ Creates invoice related analytics and financial move lines """
        account_move = self.env['account.move']

        for inv in self:
            if not inv.journal_id.sequence_id:
                raise UserError(('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line_ids:
                raise UserError(('Please create some invoice lines.'))
            if inv.move_id:
                continue

            # context = dict(self.env.context)
            # Within the context of an invoice asset with the type of the invoice.

            ctx = dict(self._context, lang=inv.partner_id.lang)
            ctx.pop('default_type', None)
            inv.invoice_line_ids.with_context(ctx).asset_create()

            if not inv.date_invoice:
                inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
            if not inv.date_due:
                inv.with_context(ctx).write({'date_due': inv.date_invoice})
            company_currency = inv.company_id.currency_id

            # create move lines (one per invoice line + eventual taxes and analytic lines)
            iml = inv.invoice_line_move_line_get()
            iml += inv.tax_line_move_line_get()

            diff_currency = inv.currency_id != company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

            name = inv.name or '/'
            if inv.payment_term_id:
                totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
                res_amount_currency = total_currency
                ctx['date'] = inv._get_currency_rate_date()
                for i, t in enumerate(totlines):
                    if inv.currency_id != company_currency:
                        amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
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
                        'account_id': inv.account_id.id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency and amount_currency,
                        'currency_id': diff_currency and inv.currency_id.id,
                        'invoice_id': inv.id
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': inv.account_id.id,
                    'date_maturity': inv.date_due,
                    'amount_currency': diff_currency and total_currency,
                    'currency_id': diff_currency and inv.currency_id.id,
                    'invoice_id': inv.id
                })
            part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
            line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
            # cancel previous receiving journal if posting in asset_id
            line += self.cancel_prev_receiving()
            if self.journal_type == 'asset_sale':
                asset_sale = inv.invoice_line_asset_sale_get(self.journal_id, inv.date_invoice)
                line += [(0, 0, a) for a in asset_sale]
            line = inv.group_lines(iml, line)

            journal = inv.journal_id.with_context(ctx)
            line = inv.finalize_invoice_move_lines(line)

            date = inv.date or inv.date_invoice
            move_vals = {
                'ref': inv.reference,
                'line_ids': line,
                'journal_id': journal.id,
                'date': date,
                'narration': inv.comment,
            }
            ctx['company_id'] = inv.company_id.id
            ctx['invoice'] = inv
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
            inv.with_context(ctx).write(vals)

        for invoice in self:
            for line in invoice.invoice_line_ids:
                if line.asset_id.id == False:
                    asset = self.env['account.asset.asset'].sudo().search([('invoice_id', '=', line.invoice_id.id), ('name', '=', line.name)])
                    for move_line in invoice.move_id.line_ids:
                        if (move_line.name == line.name and move_line.user_type_id.name == 'Fixed Assets'):
                            move_line.asset_id = asset.id
                    line.asset_id = asset.id
                else:
                    for move_line in invoice.move_id.line_ids:
                        if (move_line.name == line.name and move_line.user_type_id.name == 'Fixed Assets'):
                            move_line.asset_id = line.asset_id
            # Close asset
            if invoice.journal_type == 'asset_sale':
                invoice.invoice_line_asset_sale_closed(move.id, date)

        return True

    @api.model
    def invoice_line_asset_sale_get(self, journal_id, date):
        res = []
        for line in self.invoice_line_ids:
            if line.quantity==0:
                continue
            res.append((line.asset_id._sale_line_asset_prepare(date, line.price_subtotal, line.name)))
            loss_amount = line.asset_id._get_loss_amount()
            depreciation_value = line.asset_id.value - loss_amount
            if depreciation_value:
                res.append((line.asset_id._disposal_line_depreciation_prepare(date, depreciation_value, line.name)))
            profit_loss_amount = line.price_subtotal - line.asset_id.value_residual
            if profit_loss_amount:
                res.append((line.asset_id._sale_line_profit_loss_prepare(date, profit_loss_amount, line.name)))
            [(self.fix_sale_journal(r, journal_id)) for r in res]
        return res

    @api.model
    def invoice_line_asset_sale_closed(self, move_id, date):
        for line in self.invoice_line_ids:
            if line.quantity==0:
                continue
            line.asset_id.sale(move_id, date)

    def fix_sale_journal(self, r, journal_id):
        r['invoice_id'] = self.id
        r['journal_id'] = journal_id.id

    # @api.one
    # def asset_create(self):
    #     if self.asset_category_id:
    #         vals = {
    #             'name': self.name,
    #             'code': self.invoice_id.number or False,
    #             'category_id': self.asset_category_id.id,
    #             'value': self.price_subtotal_signed,
    #             'partner_id': self.invoice_id.partner_id.id,
    #             'company_id': self.invoice_id.company_id.id,
    #             'currency_id': self.invoice_id.company_currency_id.id,
    #             'date_acq': self.invoice_id.date_invoice,
    #             'invoice_id': self.invoice_id.id,
    #         }
    #         changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
    #         vals.update(changed_vals['value'])
    #         asset = self.env['account.asset.asset'].create(vals)
    #         if self.asset_category_id.open_asset:
    #             asset.validate()
    #     return asset

    @api.multi
    def action_cancel(self):
        res = super(AccountInvoice, self).action_cancel()
        for line in self.invoice_line_ids:
            if self.journal_type == 'asset_sale':
                line.asset_id.sale_cancel()
            elif line.asset_id:
                asset = line.asset_id
                if asset.state != 'draft':
                    raise UserError(('Cannot cancel invoice, asset not in draft state.'))
                if line.asset_id.invoice_id.id == line.invoice_id.id:
                    line.asset_id = None
                    asset.unlink()
                else:
                    amount = asset.value - line.price_subtotal_signed
                    asset.value = amount
                    # asset.purchase_value = amount
                    # print("Asset: {}".format(asset.name))
                # if line.asset_category_id:
                #     line.asset_id = None
                #     self.env['account.asset.asset'].sudo().search([('id', '=', asset.id)]).unlink()
                    # Close asset
        return res

