# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AssetDisposal(models.Model):
    _name = "account.asset.disposal"
    _description = "Asset Disposal"
    _order = "date desc, id desc"

    name = fields.Char(string='Disposal Name', index=True, required=True,
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
    disposal_line_ids = fields.One2many('account.asset.disposal.line', 'disposal_id', string='Disposal Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    @api.multi
    def _post_validate(self):
        if not self.disposal_line_ids:
            raise UserError(_('No asset selected, you cannot post a document.'))

    @api.multi
    def post(self):
        self._post_validate()
        for line in self.disposal_line_ids:
            line.asset_id.dispose(self.date, line.asset_id.category_id.account_loss_id, line.name)
        return self.write({'state': 'posted'})


    @api.multi
    def action_disposal_draft(self):
        if self.filtered(lambda disposal: disposal.state != 'cancel'):
            raise UserError(_("Invoice must be cancelled in order to reset it to draft."))
        # go from canceled state to draft state
        self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for disposal in self:
            if disposal.state in ['posted']:
                raise UserError(_('You cannot delete a document is in %s state.') % (disposal.state,))
        return super(AssetDisposal, self).unlink()

class AssetDisposalLine(models.Model):
    _name = "account.asset.disposal.line"
    _description = "Disposal Line"
    _order = "disposal_id,sequence,id"

    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(default=10,
        help="Gives the sequence of this line when displaying the invoice.")
    disposal_id = fields.Many2one('account.asset.disposal', string='Disposal Reference',
        ondelete='cascade', index=True)
    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset',
        readonly=False, ondelete='restrict', required=True,
        copy=False, index=True, auto_join=True, domain="[('state','in',['open','close'])]")
    cost_center_id = fields.Many2one("cost.center", compute='_get_asset_info', method=True, string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account', compute='_get_asset_info', method=True, string='Analytic Account')
    asset_book_value = fields.Float(compute='_get_asset_info', method=True, digits=0, string='Book Value')
    acquisition_date = fields.Date(compute='_get_asset_info', method=True, string='Tanggal Perolehan')
    acquisition_value = fields.Float(compute='_get_asset_info', method=True, digits=0, string='Nilai Perolehan')
    move_id = fields.Many2one('account.move', compute='_get_move_id', method=True, string='Journal Entry')

    _sql_constraints = [('disposal_unique',
                         'unique (asset_id)',
                         'Choose another asset - it has to be unique!')]

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        self.name = self.asset_id.name
        self._get_asset_info()

    @api.one
    def _get_asset_info(self):
        self.cost_center_id = self.asset_id.cost_center_id.id
        self.analytic_account_id = self.asset_id.analytic_account_id.id
        self.asset_book_value = self.asset_id.value_residual
        self.acquisition_date = self.asset_id.date_acq
        self.acquisition_value = self.asset_id.value

    @api.one
    def _get_move_id(self):
        self.move_id = self.asset_id.disposal_move_id.id
