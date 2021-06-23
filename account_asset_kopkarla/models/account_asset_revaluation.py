# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AssetRevaluation(models.Model):
    _name = "account.asset.revaluation"
    _description = "Asset Revaluation"
    _order = "date desc, id desc"

    name = fields.Char(string='Revaluation Name', index=True, required=True,
        readonly=True, states={'draft': [('readonly', False)]}, copy=False, help='The name that will be used on account move lines')
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([
            ('draft','Draft'),
            # ('open', 'Open'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Open' status is used when user creates invoice, an invoice number is generated. It stays in the open status till the user pays the invoice.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    date = fields.Date(string='Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    revaluation_line_ids = fields.One2many('account.asset.revaluation.line', 'revaluation_id', string='Revaluation Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    @api.multi
    def _post_validate(self):
        if not self.revaluation_line_ids:
            raise UserError(_('No asset selected, you cannot post a document.'))

    @api.multi
    def post(self):
        self._post_validate()
        for line in self.revaluation_line_ids:
            line.revaluation()
        return self.write({'state': 'posted'})

    @api.multi
    def action_revaluation_draft(self):
        if self.filtered(lambda revaluation: revaluation.state != 'cancel'):
            raise UserError(_("Invoice must be cancelled in order to reset it to draft."))
        # go from canceled state to draft state
        self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for revaluation in self:
            if revaluation.state in ['posted']:
                raise UserError(_('You cannot delete a document is in %s state.') % (revaluation.state,))
        return super(AssetRevaluation, self).unlink()

class AssetRevaluationLine(models.Model):
    _name = "account.asset.revaluation.line"
    _description = "Revaluation Line"
    _order = "revaluation_id,sequence,id"

    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(default=10,
        help="Gives the sequence of this line when displaying the invoice.")
    revaluation_id = fields.Many2one('account.asset.revaluation', string='Revaluation Reference',
        ondelete='cascade', index=True)
    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset',
        readonly=False, ondelete='restrict', required=True,
        copy=False, index=True, auto_join=True, domain="[('state','in',['open','close'])]")
    cost_center_id = fields.Many2one("cost.center", compute='_get_asset_info', method=True, string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account', compute='_get_asset_info', method=True, string='Analytic Account')
    current_book_value = fields.Float(compute='_get_asset_info', method=True, digits=0, string='Current Value', store=True)
    adjustment_value = fields.Float(string='Adjustment', required=True, digits=0, states={'draft': [('readonly', False)]})
    book_value = fields.Float(compute='_calculate_book_value', method=True, digits=0, string='Book Value', store=True)
    move_id = fields.Many2one(comodel_name='account.move', string="Revaluation Journal",)

    @api.one
    @api.depends('adjustment_value')
    def _calculate_book_value(self):
        self.book_value = self.current_book_value + self.adjustment_value

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        self.name = self.asset_id.name
        self._get_asset_info()

    @api.one
    def _get_asset_info(self):
        self.cost_center_id = self.asset_id.cost_center_id.id
        self.analytic_account_id = self.asset_id.analytic_account_id.id
        self.current_book_value = self.asset_id.value_residual

    # @api.one
    # def _get_move_id(self):
    #     self.move_id = self.asset_id.revaluation_move_id.id

    def _revaluation_prepare(self):
        self.ensure_one()
        journal = self.asset_id.category_id.journal_reval_id
        lines = [(0, False, self._adjust_acqusition_prepare()),
                 (0, False, self._adjust_expense_prepare())]
        # create asset
        return {
            'journal_id': journal.id,
            'ref': "Revaluation of asset {}".format(self.name),
            'date': self.revaluation_id.date,
            'line_ids': lines,
        }

    def _adjust_expense_prepare(self):
        self.ensure_one()
        vals = {
            'name': self.name,
            # 'asset_id': asset_id.id,
            # 'journal_id': asset_id.category_id.journal_reclass_id.id,
            'account_id': self.adjustment_value > 0 and self.asset_id.category_id.account_profit_id.id or self.asset_id.category_id.account_loss_id.id,
            'date': self.revaluation_id.date,
            'debit': self.adjustment_value < 0 and abs(self.adjustment_value),
            'credit': self.adjustment_value > 0 and self.adjustment_value,
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id

        return vals

    def _adjust_acqusition_prepare(self):
        self.ensure_one()
        vals = {
            'name': self.name,
            'asset_id': self.asset_id.id,
            # 'journal_id': self.category_id.journal_reclass_id.id,
            'account_id': self.asset_id.category_id.account_asset_id.id,
            'date': self.revaluation_id.date,
            'debit': self.adjustment_value > 0 and self.adjustment_value,
            'credit': self.adjustment_value < 0 and abs(self.adjustment_value),
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id

        return vals

    @api.multi
    def revaluation(self):
        moves = self.env['account.move']
        if self.adjustment_value:
            move = self.env['account.move'].create(
                self._revaluation_prepare()
            )
            move.post()
            self.move_id = move.id
            self.asset_id.revaluation(self.adjustment_value)

            # self.message_post(body=_('Asset revaluation.'))
            moves += move

        if moves:
            name = _('Reclass Move')
            view_mode = 'form'
            if len(moves) > 1:
                name = _('Revaluation Moves')
                view_mode = 'tree,form'
            return {
                'name': name,
                'domain': [('id', 'in', moves.ids)],
                'view_type': 'form',
                'view_mode': view_mode,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': moves[:1].id,
            }

    @api.multi
    def action_revaluation_undo(self):
        self.asset_id.revaluation(-self.adjustment_value)
        self.move_id.button_cancel()
        self.move_id.unlink()
