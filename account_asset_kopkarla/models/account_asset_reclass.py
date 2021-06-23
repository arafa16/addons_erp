# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AssetReclass(models.Model):
    _name = "account.asset.reclass.table"
    _description = "Asset Reclass"
    _order = "date desc, id desc"

    name = fields.Char(string='Reclass Name', index=True, required=True,
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
             " * The 'Posted' status is set automatically when the asset is posted. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    date = fields.Date(string='Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    reclass_line_ids = fields.One2many('account.asset.reclass.line', 'reclass_id', string='Reclass Lines',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    @api.multi
    def _post_validate(self):
        if not self.reclass_line_ids:
            raise UserError(_('No asset selected, you cannot post a document.'))
        i = 0
        for line in self.reclass_line_ids:
            i += 1
            if line.asset_id_to:
                if line.asset_id == line.asset_id_to:
                    raise UserError(_('Reclass "%s. %s" to itself is not permitted.') % (i, line.asset_id.name))
            else:
                if not line.category_id_to:
                    raise UserError(_('New category is not selected yet for "%s. %s".') % (i, line.asset_id.name))
                elif line.category_id == line.category_id_to:
                    raise UserError(_('Change to a different category for "%s. %s".') % (i, line.asset_id.name))

    @api.multi
    def post(self):
        self._post_validate()
        for line in self.reclass_line_ids:
            line.asset_id.reclass(line.asset_id_to, line.category_id, line.category_id_to, self.date, line.name)
            # if line.asset_id_to:
            #     # close old asset
            #
            # # else:
            old_values = {
                'category_id': line.category_id.id,
                'method_number': line.category_id.method_number,
                'method_period': line.category_id.method_period,
            }
            asset_vals = {
                'category_id': line.category_id_to.id,
                'method_number': line.category_id_to.method_number,
                'method_period': line.category_id_to.method_period,
            }
            line.asset_id.write(asset_vals)
            line.asset_id.compute_depreciation_board()
            tracked_fields = self.env['account.asset.asset'].fields_get(['category', 'method_number', 'method_period'])
            changes, tracking_value_ids = line.asset_id._message_track(tracked_fields, old_values)
            if changes:
                line.asset_id.message_post(subject=_('Depreciation board modified'), body=self.name,
                                   tracking_value_ids=tracking_value_ids)
        return self.write({'state': 'posted'})

    @api.multi
    def action_reclass_draft(self):
        if self.filtered(lambda reclass: reclass.state != 'cancel'):
            raise UserError(_("Document must be cancelled in order to reset it to draft."))
        # go from canceled state to draft state
        self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for disposal in self:
            if disposal.state in ['posted']:
                raise UserError(_('You cannot delete a document is in %s state.') % (disposal.state,))
        return super(AssetReclass, self).unlink()

class AssetReclassLine(models.Model):
    _name = "account.asset.reclass.line"
    _description = "Reclass Line"
    _order = "reclass_id,sequence,id"

    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(default=10,
        help="Gives the sequence of this line when displaying the asset reclass.")
    reclass_id = fields.Many2one('account.asset.reclass.table', string='Reclass Reference',
        ondelete='cascade', index=True)
    asset_id = fields.Many2one('account.asset.asset', 'Asset', readonly=False, ondelete='restrict', copy=False,
                               required=True, index=True, auto_join=True, domain="[('state','in',['open','close'])]")
    category_id = fields.Many2one('account.asset.category', string='Category', ondelete='restrict')
    category_id_to = fields.Many2one('account.asset.category', string='To Category', ondelete='restrict', change_default=True, states={'draft': [('readonly', False)]})
    asset_id_to = fields.Many2one('account.asset.asset', 'To Asset', ondelete='restrict', copy=False, index=True, auto_join=True, domain="[('state','in',['open','close'])]")
    cost_center_id = fields.Many2one("cost.center", compute='_get_asset_info', method=True, string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account', compute='_get_asset_info', method=True, string='Analytic Account')
    asset_book_value = fields.Float(compute='_get_asset_info', method=True, digits=0, string='Book Value')
    move_id = fields.Many2one('account.move', compute='_get_move_id', method=True, string='Journal Entry')

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        self.name = self.asset_id.name
        self.category_id = self.asset_id.category_id.id
        self._get_asset_info()

    @api.one
    def _get_asset_info(self):
        if self.asset_id:
            self.cost_center_id = self.asset_id.cost_center_id.id
            self.analytic_account_id = self.asset_id.analytic_account_id.id
            self.asset_book_value = self.asset_id.value_residual

    @api.one
    def _get_move_id(self):
        self.move_id = self.asset_id.reclass_move_id.id

    @api.onchange('asset_id_to')
    def _onchange_asset_id_to(self):
        self.category_id_to = self.asset_id_to.category_id.id
