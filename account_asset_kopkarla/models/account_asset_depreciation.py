# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools import float_compare

class AssetDepreciation(models.Model):
    _name = "account.asset.depreciation"
    _description = "Asset Depreciation"
    _order = "date desc, id desc"

    name = fields.Char(string='Depreciation Name', index=True, required=True,
        readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
            ('draft','Draft'),
            # ('open', 'Open'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,)
    date = fields.Date(string='Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    depreciation_line_ids = fields.One2many('account.asset.depreciation.line', 'depreciation_id', string='Depreciation Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    lines = fields.Integer(string='Lines', compute='get_total_depreciation', method=True)
    total = fields.Float(string='Total Depreciation', digits=0, compute='get_total_depreciation', method=True)
    move_id = fields.Many2one('account.move', string='Depreciation Entry', ondelete="set null", readonly=True)

    @api.one
    def get_total_depreciation(self):
        total = 0
        lines = 0
        for line in self.depreciation_line_ids:
            lines += 1
            total += line.amount
        self.lines = lines
        self.total = total

    @api.multi
    def get_asset(self):
        depreciation_lines = self.env['account.asset.depreciation.line'].search([('depreciation_id', '=', False), ('move_check', '=', False), ('parent_state', '=', 'open'),
                                    ('depreciation_date', '<=', (datetime.date(datetime.strptime(self.date, "%Y-%m-%d")).replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1))])
        for line in depreciation_lines:
            line.depreciation_id = self.id
            line.move_check = True

    @api.multi
    def clear_asset(self):
        for line in self.depreciation_line_ids:
            line.depreciation_id = False
            line.move_check = False

    @api.multi
    def _post_validate(self):
        if not self.depreciation_line_ids:
            raise UserError(_('No asset selected, you cannot post a document.'))

    # @api.multi
    # def post(self):
    #     self._post_validate()
    #     for line in self.depreciation_line_ids:
    #         line.depreciation_date = self.date
    #         line.create_move()
    #     return self.write({'state': 'posted'})

    def line_hashcode(self, line):
        """Overridable hashcode generation for invoice lines. Lines having the same hashcode
        will be grouped together if the journal has the 'group line' option. Of course a module
        can add fields to invoice lines that would need to be tested too before merging lines
        or not."""
        return "%s-%s-%s-%s" % (
            line['category'],
            line['account_id'],
            # line.get('tax_ids', 'False'),
            # line.get('tax_line_id', 'False'),
            line.get('cost_center_id', 'False'),
            line.get('analytic_account_id', 'False'),
            # line.get('date_maturity', 'False'),
            # line.get('analytic_tag_ids', 'False'),
        )

    def group_depre_journal(self, line):
        return {
            'name': "Depresiasi %s" % line['category'],
            # 'name': "%s - %s - %s" % (line['name'], line.get('cost_center_id', 'False'), line.get('analytic_account_id', 'False')),
            'account_id': line['account_id'],
            'cost_center_id': line.get('cost_center_id', False),
            'analytic_account_id': line.get('analytic_account_id', False),
            'debit': line['debit'],
            'credit': line['credit'],
            'currency_id': line['currency_id'],
            'amount_currency': line['amount_currency'],
        }

    def group_lines(self, lines):
        """Merge account move lines (and hence analytic lines) if invoice line hashcodes are equals"""
        # if self.journal_id.group_invoice_lines:
        line2 = {}
        depre = {}
        for l in lines:
            tmp = self.line_hashcode(l)
            if l.get('asset_id', False):
                if tmp not in depre:
                    depre[tmp] = [(0, 0, l)]
                else:
                    depre[tmp].append((0, 0, l))
            if tmp in line2:
                am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                line2[tmp]['debit'] = (am > 0) and am or 0.0
                line2[tmp]['credit'] = (am < 0) and -am or 0.0
                line2[tmp]['amount_currency'] += l['amount_currency']
                # line2[tmp]['analytic_line_ids'] += l['analytic_line_ids']
                # qty = l.get('quantity')
                # if qty:
                #     line2[tmp]['quantity'] = line2[tmp].get('quantity', 0.0) + qty
            else:
                line2[tmp] = self.group_depre_journal(l)

        # dpr = (0, 0, d) for d in depre
        for key, dep in depre.items():
            line2[key]['depre_lines'] = dep
        keys = [l[0] for l in line2.items()]
        keys.sort()
        line = []
        for key in keys:
            line.append(line2[key])
        return line #, depre

    @api.multi
    def post(self):
        self._post_validate()
        created_moves = self.env['account.move']
        prec = self.env['decimal.precision'].precision_get('Account')
        lines = []
        for line in self.depreciation_line_ids:
            # line.depreciation_date = self.date

            category_id = line.asset_id.category_id
            depreciation_date = self.env.context.get(
                'depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            amount = current_currency.with_context(date=depreciation_date).compute(line.amount, company_currency)
            asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
            asset_id = line.asset_id.id
            partner = self.env['res.partner']._find_accounting_partner(line.asset_id.partner_id)
            lines.append({
                'name': asset_name,
                'asset_id': asset_id,
                'category': category_id.name,
                'account_id': category_id.account_depreciation_id.id,
                'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                # 'journal_id': category_id.journal_id.id,
                # 'partner_id': partner.id,
                # 'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
                'cost_center_id': line.asset_id.cost_center_id.id,
                'analytic_account_id': line.asset_id.analytic_account_id.id,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
            })
            lines.append({
                'name': asset_name,
                # 'asset_id': asset_id,
                'category': category_id.name,
                'account_id': category_id.account_depreciation_expense_id.id,
                'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
                'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
                # 'journal_id': category_id.journal_id.id,
                # 'partner_id': partner.id,
                'cost_center_id': line.asset_id.cost_center_id.id,
                'analytic_account_id': line.asset_id.analytic_account_id.id,
                'currency_id': company_currency != current_currency and current_currency.id or False,
                'amount_currency': company_currency != current_currency and line.amount or 0.0,
            })

        # lns = lines
        lns = self.group_lines(lines)
        move_lines = [(0, 0, line) for line in lns]

        move_vals = {
            'ref': line.asset_id.code,
            'date': depreciation_date or False,
            'ref': self.description,
            'journal_id': category_id.journal_id.id,
            'line_ids': move_lines,
        }
        move = self.env['account.move'].create(move_vals)
        if move:
            move.post()
        for line in self.depreciation_line_ids:
            line.depreciation_date = self.date
            line.move_posted_check = True

        return self.write({'move_id': move.id, 'state': 'posted'})

    # def create_move(self, post_move=True):
    #
    #     if self.mapped('move_id'):
    #         raise UserError(_('This depreciation is already linked to a journal entry! Please post or delete it.'))
    #     for line in self:
    #         # if 'cost_center_id' in line.asset_id:
    #         #     move_line_1['cost_center_id'] = move_line_2['cost_center_id'] = line.asset_id.cost_center_id.id
    #
    #
    #         line.write({'move_id': move.id, 'move_check': True})
    #         created_moves |= move
    #
    #     if post_move and created_moves:
    #         created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
    #     return [x.id for x in created_moves]

    @api.multi
    def action_depreciation_draft(self):
        if self.filtered(lambda depreciation: depreciation.state != 'cancel'):
            raise UserError(_("Invoice must be cancelled in order to reset it to draft."))
        # go from canceled state to draft state
        self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for depreciation in self:
            if depreciation.state in ['posted']:
                raise UserError(_('You cannot delete a document is in %s state.') % (depreciation.state,))
            for line in depreciation.depreciation_line_ids:
                line.move_check = False
        return super(AssetDepreciation, self).unlink()

    @api.multi
    def action_depreciation_undo(self):
        for line in self.depreciation_line_ids:
            line.move_posted_check = False
        if self.move_id:
            self.move_id.button_cancel()
            self.move_id.unlink()

class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    cost_center_id = fields.Many2one("cost.center", compute='_get_asset_info', method=True, string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', compute='_get_asset_info', method=True)
    depreciation_id = fields.Many2one('account.asset.depreciation', string='Depreciation Reference', ondelete='set null', index=True)
    depreciation_date_org = fields.Date('Depreciation Date Plan', index=True)

    # @api.multi
    # def create_move(self, post_move=True):
    #     created_moves = self.env['account.move']
    #     prec = self.env['decimal.precision'].precision_get('Account')
    #     if self.mapped('move_id'):
    #         raise UserError(_('This depreciation is already linked to a journal entry! Please post or delete it.'))
    #     for line in self:
    #         category_id = line.asset_id.category_id
    #         depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
    #         company_currency = line.asset_id.company_id.currency_id
    #         current_currency = line.asset_id.currency_id
    #         amount = current_currency.with_context(date=depreciation_date).compute(line.amount, company_currency)
    #         asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
    #         asset_id = line.asset_id.id
    #         partner = self.env['res.partner']._find_accounting_partner(line.asset_id.partner_id)
    #         move_line_1 = {
    #             'name': asset_name,
    #             'asset_id': asset_id,
    #             'account_id': category_id.account_depreciation_id.id,
    #             'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
    #             'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
    #             'journal_id': category_id.journal_id.id,
    #             'partner_id': partner.id,
    #             'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
    #             'currency_id': company_currency != current_currency and current_currency.id or False,
    #             'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
    #         }
    #
    #         move_line_2 = {
    #             'name': asset_name,
    #             'account_id': category_id.account_depreciation_expense_id.id,
    #             'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
    #             'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
    #             'journal_id': category_id.journal_id.id,
    #             'partner_id': partner.id,
    #             'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
    #             'currency_id': company_currency != current_currency and current_currency.id or False,
    #             'amount_currency': company_currency != current_currency and line.amount or 0.0,
    #         }
    #         if 'cost_center_id' in line.asset_id:
    #             move_line_1['cost_center_id'] = move_line_2['cost_center_id'] = line.asset_id.cost_center_id.id
    #
    #         move_vals = {
    #             'ref': line.asset_id.code,
    #             'date': depreciation_date or False,
    #             'journal_id': category_id.journal_id.id,
    #             'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
    #         }
    #         move = self.env['account.move'].create(move_vals)
    #         line.write({'move_id': move.id, 'move_check': True})
    #         created_moves |= move
    #
    #     if post_move and created_moves:
    #         created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
    #     return [x.id for x in created_moves]

    @api.multi
    def unlink(self):
        if self.depreciation_id:
            self.depreciation_id = False
            self.move_check = False
        else:
            super(AccountAssetDepreciationLine, self).unlink()

    @api.one
    def _get_asset_info(self):
        self.cost_center_id = self.asset_id.cost_center_id.id
        self.analytic_account_id = self.asset_id.analytic_account_id.id
        # self.asset_book_value = self.asset_id.value_residual

    # @api.multi
    # def action_depreciation_undo(self):
    #     if self.move_id:
    #         if self.move_posted_check:
    #             self.move_id.button_cancel()
    #             self.move_posted_check = False
    #         if self.move_check:
    #             self.move_id.unlink()
    #             self.move_check = False
    #         self.restore_deprecation_date()

    # def restore_deprecation_date(self):
    #     self.depreciation_date = self.depreciation_date_org
