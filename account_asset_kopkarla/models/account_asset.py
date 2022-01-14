from odoo import api, fields, models, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    date_acq = fields.Date(string='Acquisition Date', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Date.context_today)
    date = fields.Date(string='Start Period', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Date.context_today, oldname="purchase_date")
    code = fields.Char(string='Reference', size=32, readonly=True, states={'draft': [('readonly', False)]}, required=True)
    cost_center_id = fields.Many2one("cost.center", string='Cost Center', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    account_move_line_ids = fields.One2many(
        'account.move.line', 'asset_id', 'Journal Items',
        readonly=True, copy=False)
    state = fields.Selection(
        selection_add=[('disposed', 'Disposed'), ('sale', 'Sale'), ('reclass', 'Reclass')],
    )
    disposal_date = fields.Date(string="Disposal date")
    disposal_move_id = fields.Many2one(
        comodel_name='account.move', string="Disposal Journal",
    )
    reclass_to_asset_id = fields.Many2one('account.asset.asset', 'Reclass to asset', readonly=False,
                                            ondelete='restrict', copy=False, index=True, auto_join=True)
    reclass_date = fields.Date(string="Reclass date")
    reclass_move_id = fields.Many2one(
        comodel_name='account.move', string="Reclass Journal",
    )
    sale_date = fields.Date(string="Sale date")
    sale_move_id = fields.Many2one(
        comodel_name='account.move', string="Sale Journal",
    )

    allow_reclass = fields.Boolean(compute='_compute_allow_reclass')

    _fields_to_compute = ['value_residual']

    _sql_constraints = [('asset_unique',
                         'unique (code)',
                         'Choose another reference - it has to be unique!')]
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        fields_to_compute = []
        for field in self._fields_to_compute:
            if field in fields:
                fields.remove(field)
                fields_to_compute.append(field)
        res = super(AccountAssetAsset, self).read_group(
            domain, fields, groupby, offset, limit, orderby, lazy)
        if fields_to_compute:
            for group in res:
                if group.get('__domain'):
                    line_infos = self.search_read(group['__domain'],
                                                  fields_to_compute)
                    for field in fields_to_compute:
                        group[field] = sum([l[field] for l in line_infos])
        return res

    @api.onchange('date_acq')
    def _onchange_date_acq(self):
        date_acq = datetime.strptime(self.date_acq, DF).date()
        self.date = date_acq.day <= 15 and date_acq.replace(day=1) or date_acq.replace(day=1) + relativedelta(months=1)

    def _compute_allow_reclass(self):
        self.allow_reclass = True # (self.category_id.asset_in_progress == True)

    @api.one
    @api.depends('value', 'salvage_value', 'depreciation_line_ids.move_check', 'depreciation_line_ids.amount')
    def _amount_residual(self):
        total_amount = 0.0
        # depreciations = self.depreciation_line_ids.filtered(lambda depre: depre.move_check == True)
        depreciations = self.env['account.asset.depreciation.line'].search([('asset_id', '=', self.id),
                                                                            ('move_check', '=', True)])
        for line in depreciations:
            # if line.move_check:
            total_amount += line.amount
        self.value_residual = self.value - total_amount - self.salvage_value

    def _disposal_line_asset_prepare(self, date, txt = ''):
        self.ensure_one()
        vals = {
            # 'name': _('Reverse acquisition value of asset {}'.format(self.name)),
            'name': txt,
            'asset_id': self.id,
            'journal_id': self.category_id.journal_disp_id.id,
            'account_id': self.category_id.account_asset_id.id,
            'date': date,
            'debit': 0.0,
            'credit': self.value,
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id

        return vals

    def _sale_line_asset_prepare(self, date, sale_price, txt = ''):
        self.ensure_one()
        vals = {
            # 'name': _('Reverse asset sale'),
            'name': txt,
            'asset_id': self.id,
            'journal_id': self.category_id.journal_disp_id.id,
            'account_id': self.category_id.account_asset_id.id,
            'date': date,
            'debit': self.value < sale_price and sale_price - self.value,
            'credit': self.value > sale_price and self.value - sale_price,
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id

        return vals

    def _get_loss_amount(self):
        self.ensure_one()
        loss_value = self.salvage_value
        if not float_is_zero(self.value_residual,
                             precision_rounding=self.currency_id.rounding):
            loss_value += self.value_residual
        return loss_value

    def _disposal_line_depreciation_prepare(self, date, depreciation_value, txt = ''):
        vals = {
            # 'name': _('Reverse accumulation depreciation of asset {}'.format(self.name)),
            'name': txt,
            'asset_id': self.id,
            'journal_id': self.category_id.journal_disp_id.id,
            'account_id': self.category_id.account_depreciation_id.id,
            'date': date,
            'debit': depreciation_value,
            'credit': 0.0,
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id

        return vals

    def _disposal_loss_prepare(self, date, loss_account, loss_amount, txt = ''):
        vals = {
            'name': txt,
            'journal_id': self.category_id.journal_disp_id.id,
            'account_id': loss_account.id,
            'analytic_account_id': self.category_id.account_analytic_id.id,
            'date': date,
            'debit': loss_amount,
            'credit': 0.0,
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id
        return vals

    def _add_reclass_prepare(self, date, asset_id, amount, txt = ''):
        self.ensure_one()
        vals = {
            'name': txt,
            'asset_id': asset_id.id,
            # 'journal_id': asset_id.category_id.journal_reclass_id.id,
            'account_id': asset_id.category_id.account_asset_id.id,
            'date': date,
            'debit': amount,
            'credit': 0.0,
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id

        return vals

    def _remove_reclass_prepare(self, date, loss_amount, txt = ''):
        self.ensure_one()
        vals = {
            'name': txt,
            'asset_id': self.id,
            # 'journal_id': self.category_id.journal_reclass_id.id,
            'account_id': self.category_id.account_asset_id.id, #self.category_id.account_asset_id.id,
            'date': date,
            'debit': 0.0,
            'credit': loss_amount,
        }
        if 'cost_center_id' in self:
            vals['cost_center_id'] = self.cost_center_id.id

        return vals

    def _sale_line_profit_loss_prepare(self, date, profit_loss_amount, txt = ''):
        self.ensure_one()
        vals = {
            # 'name': profit_loss_amount > 0 and "Asset profit sale" or "Asset loss sale", #_('Asset loss'),
            'name': txt, #_('Asset loss'),
            'journal_id': self.category_id.journal_disp_id.id,
            'account_id': profit_loss_amount > 0 and self.category_id.account_profit_id.id or self.category_id.account_loss_id.id,
            'cost_center_id': self.cost_center_id.id,
            'analytic_account_id': self.analytic_account_id.id,
            'date': date,
            'debit': profit_loss_amount < 0 and abs(profit_loss_amount),
            'credit': profit_loss_amount > 0 and profit_loss_amount,
        }

        return vals

    def _disposal_move_prepare(self, date, loss_account, txt = ''):
        self.ensure_one()
        journal = self.category_id.journal_disp_id
        lines = [(0, False, self._disposal_line_asset_prepare(date, txt))]
        # depreciation_value = self._get_accumulation_depreciation()
        loss_amount = self._get_loss_amount()
        depreciation_value = self.value - loss_amount
        if depreciation_value:
            lines.append((0, False, self._disposal_line_depreciation_prepare(date, depreciation_value, txt)))
        if loss_amount:
            lines.append((0, False, self._disposal_loss_prepare(date, loss_account, loss_amount, txt)))
        return {
            'journal_id': journal.id,
            'ref': "Dispose of asset {}".format(self.name),
            'date': date,
            'line_ids': lines,
        }

    @api.multi
    def action_disposal(self):
        wizard_view_id = self.env.ref(
            'account_asset_kopkarla.account_asset_disposal_wizard_form')
        return {
            'name': _('Dispose Asset'),
            'res_model': 'account.asset.disposal.wizard',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'view_mode': 'form',
            'view_id': wizard_view_id.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def dispose(self, date, loss_account, txt = ''):
        moves = self.env['account.move']
        for asset in self:
            move = self.env['account.move'].create(
                asset._disposal_move_prepare(date, loss_account, txt)
            )
            asset.disposal_move_id = move.id
            move.post()
            unposted_lines = asset.depreciation_line_ids.filtered(
                lambda x: not x.move_check
            )
            if unposted_lines:
                # Remove all unposted depreciation lines
                asset.write({
                    'depreciation_line_ids': [
                        (2, line_id.id) for line_id in unposted_lines
                    ],
                })
            # Create a new depr. line with the residual amount and post it
            sequence = (
                    len(asset.depreciation_line_ids) - len(unposted_lines) + 1
            )
            vals = {
                'amount': asset.value_residual,
                'asset_id': asset.id,
                'sequence': sequence,
                'name': (asset.code or '') + '/' + str(sequence),
                'remaining_value': 0,
                # the asset is completely depreciated
                'depreciated_value': asset.value - asset.salvage_value,
                'depreciation_date': date,
                'move_id': move.id,
            }

            asset.depreciation_line_ids.create(vals)
            asset.message_post(body=_('Asset disposed.'))
            moves += move
        self.write({
            'disposal_date': date,
            'state': 'disposed',
        })
        if moves:
            name = _('Disposal Move')
            view_mode = 'form'
            if len(moves) > 1:
                name = _('Disposal Moves')
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

    def dispose_move_line(self, date, loss_account):
        moves = self.env['account.move']
        for asset in self:
            move = self.env['account.move'].create(
                asset._disposal_move_prepare(date, loss_account)
            )
            asset.disposal_move_id = move.id
            move.post()
            unposted_lines = asset.depreciation_line_ids.filtered(
                lambda x: not x.move_check
            )
            if unposted_lines:
                # Remove all unposted depreciation lines
                asset.write({
                    'depreciation_line_ids': [
                        (2, line_id.id) for line_id in unposted_lines
                    ],
                })
            # Create a new depr. line with the residual amount and post it
            sequence = (
                    len(asset.depreciation_line_ids) - len(unposted_lines) + 1
            )
            vals = {
                'amount': asset.value_residual,
                'asset_id': asset.id,
                'sequence': sequence,
                'name': (asset.code or '') + '/' + str(sequence),
                'remaining_value': 0,
                # the asset is completely depreciated
                'depreciated_value': asset.value - asset.salvage_value,
                'depreciation_date': date,
                'move_id': move.id,
            }

            asset.depreciation_line_ids.create(vals)
            asset.message_post(body=_('Asset disposed.'))
            moves += move
        self.write({
            'disposal_date': date,
            'state': 'disposed',
        })
        if moves:
            name = _('Disposal Move')
            view_mode = 'form'
            if len(moves) > 1:
                name = _('Disposal Moves')
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
    def action_disposal_undo(self):
        for asset in self.with_context(asset_disposal_undo=True):
            if asset.disposal_move_id:
                asset.disposal_move_id.button_cancel()
                asset.disposal_move_id.unlink()
            asset.depreciation_line_ids[-1].unlink()
            if asset.currency_id.is_zero(asset.value_residual):
                asset.state = 'close'
            else:
                asset.state = 'open'
                asset.compute_depreciation_board()
            asset.message_post(body=_('Asset disposal cancelled.'))
        return self.write({
            'disposal_date': False,
            'disposal_move_id': False,
        })

    def _reclass_to_asset_move_prepare(self, date, to_asset, amount, txt):
        self.ensure_one()
        journal = self.category_id.journal_reclass_id
        lines = [(0, False, self._remove_reclass_prepare(date, amount, txt)),
                 (0, False, self._add_reclass_prepare(date, to_asset, amount, txt))]
        # create asset
        return {
            'journal_id': journal.id,
            'ref': "Dispose of asset {}".format(self.name),
            'date': date,
            'line_ids': lines,
        }

    def _reclass_to_asset_move(self, to_asset, date, txt):
        moves = self.env['account.move']
        # for asset in self:
        loss_amount = self._get_loss_amount()
        if loss_amount:
            move = self.env['account.move'].create(
                self._reclass_to_asset_move_prepare(date, to_asset, loss_amount, txt)
            )
            self.reclass_move_id = move.id
            move.post()
            # clear book value of asset
            unposted_lines = self.depreciation_line_ids.filtered(
                lambda x: not x.move_check
            )
            if unposted_lines:
                # Remove all unposted depreciation lines
                self.write({
                    'depreciation_line_ids': [
                        (2, line_id.id) for line_id in unposted_lines
                    ],
                })
            # Create a new depr. line with the residual amount and post it
            sequence = (
                    len(self.depreciation_line_ids) - len(unposted_lines) + 1
            )
            vals = {
                'amount': self.value_residual,
                'asset_id': self.id,
                'sequence': sequence,
                'name': (self.code or '') + '/' + str(sequence),
                'remaining_value': 0,
                # the asset is completely depreciated
                'depreciated_value': self.value - self.salvage_value,
                'depreciation_date': date,
                'move_id': move.id,
            }
            self.depreciation_line_ids.create(vals)

            # Reclass amount to destination asset_id
            to_asset.value += loss_amount
            if to_asset.currency_id.is_zero(to_asset.value_residual):
                to_asset.state = 'close'
            else:
                to_asset.state = 'open'
                to_asset.compute_depreciation_board()


            self.message_post(body=_('Asset reclass.'))
            moves += move
            self.write({
                'reclass_to_asset_id': to_asset.id,
                'reclass_date': date,
                'state': 'reclass',
            })

        if moves:
            name = _('Reclass Move')
            view_mode = 'form'
            if len(moves) > 1:
                name = _('Reclass Moves')
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
    def reclass(self, to_asset, from_category, to_category, date, txt):
        debit = credit = self.currency_id.compute(self.value_residual, self.currency_id)
        if to_asset:
            self._reclass_to_asset_move(to_asset, date, txt)
        else:
            if self.state in ['open', 'close']:
                # sequence_code = 'hr.advance.sequence'
                # rec.name = self.env['ir.sequence'].with_context(ir_sequence_date=rec.payment_date).next_by_code(sequence_code)
                # sequence_code = 'account.asset.reclass.sequence'
                # journal_name = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
                move = {
                    # 'name': to_category.journal_reclass_id.name, # journal_name,
                    'journal_id': to_category.journal_reclass_id.id,
                    'date': date,
                    'ref': "Reclass asset {} from category {} to {}".format(self.name, from_category.name, to_category.name),
                    'line_ids': [(0, 0, {
                        'name': txt,
                        'debit': debit,
                        'account_id': to_category.account_asset_id.id,
                        'asset_id': self.id,
                        # 'partner_id': asset.employee_id.user_id.partner_id.id,
                    }), (0, 0, {
                        'name': txt,
                        'credit': credit,
                        'account_id': from_category.account_asset_id.id,
                        'asset_id': self.id,
                        # 'partner_id': asset.employee_id.user_id.partner_id.id,
                    })]
                }
                if 'cost_center_id' in self:
                    move['line_ids'][0][2]['cost_center_id'] = move['line_ids'][1][2]['cost_center_id'] = self.cost_center_id.id

                move_id = self.env['account.move'].create(move)
                move_id.post()
                return self.write({'reclass_date': date, 'reclass_move_id': move_id.id})

    @api.multi
    def action_reclass_undo(self, asset_id_to, from_category, to_category):
        asset_reclass_amount = self.depreciation_line_ids[-1].amount
        if asset_id_to:
            asset_to_residual_amount = asset_id_to.value_residual
            if asset_to_residual_amount < asset_reclass_amount:
                raise UserError(_('You cannot cancel reclass asset %s due to insufficient book value of destination asset.') % (self.name,))

        if self.reclass_move_id:
            self.reclass_move_id.button_cancel()
            self.reclass_move_id.unlink()
        self.depreciation_line_ids[-1].unlink()
        if self.currency_id.is_zero(self.value_residual):
            self.state = 'close'
        else:
            self.state = 'open'
            self.compute_depreciation_board()
        if asset_id_to:
            acquisition_amount = asset_id_to.value - asset_reclass_amount
            asset_id_to.value = acquisition_amount
            if asset_id_to.currency_id.is_zero(asset_id_to.value_residual):
                asset_id_to.state = 'close'
            else:
                asset_id_to.state = 'open'
                asset_id_to.compute_depreciation_board()

        self.message_post(body=_('Asset reclass cancelled.'))
        return self.write({
            'reclass_to_asset_id': False,
            'reclass_date': False,
            'reclass_move_id': False,
        })

    @api.multi
    def sale(self, move_id, date):
        unposted_lines = self.depreciation_line_ids.filtered(
            lambda x: not x.move_check
        )
        if unposted_lines:
            # Remove all unposted depreciation lines
            self.write({
                'depreciation_line_ids': [
                    (2, line_id.id) for line_id in unposted_lines
                ],
            })
        # Create a new depr. line with the residual amount and post it
        sequence = (
                len(self.depreciation_line_ids) - len(unposted_lines) + 1
        )
        vals = {
            'amount': self.value_residual,
            'asset_id': self.id,
            'sequence': sequence,
            'name': (self.code or '') + '/' + str(sequence),
            'remaining_value': 0,
            # the asset is completely depreciated
            'depreciated_value': self.value - self.salvage_value,
            'depreciation_date': date,
            'move_id': move_id,
        }

        self.depreciation_line_ids.create(vals)
        self.message_post(body=_('Asset sale.'))
        self.write({
            'sale_move_id': move_id,
            'sale_date': date,
            'state': 'sale',
        })

    @api.multi
    def sale_cancel(self):
        if self.sale_date:
            self.sale_move_id.button_cancel()
            self.sale_move_id.unlink()
            self.depreciation_line_ids[-1].unlink()
            if self.currency_id.is_zero(self.value_residual):
                self.state = 'close'
            else:
                self.state = 'open'
                self.compute_depreciation_board()
                self.message_post(body=_('Asset sale cancelled.'))
            return self.write({
                'sale_date': False,
                'sale_move_id': False,
            })

    @api.multi
    def compute_depreciation_board(self):
        self.ensure_one()

        posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
        unposted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_check)

        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

        if self.value_residual != 0.0:
            amount_to_depr = residual_amount = self.value_residual
            if self.prorata:
                # if we already have some previous validated entries, starting date is last entry + method perio
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    depreciation_date = datetime.strptime(self._get_last_depreciation_date()[self.id], DF).date()
            else:
                # depreciation_date = 1st of January of purchase year if annual valuation, 1st of
                # purchase month in other cases
                if self.method_period >= 12:
                    if self.company_id.fiscalyear_last_month:
                        asset_date = date(year=int(self.date[:4]),
                                                   month=self.company_id.fiscalyear_last_month,
                                                   day=self.company_id.fiscalyear_last_day) + \
                                     relativedelta(days=1) + \
                                     relativedelta(year=int(self.date[:4]))  # e.g. 2018-12-31 +1 -> 2019
                    else:
                        asset_date = datetime.strptime(self.date[:4] + '-01-01', DF).date()
                else:
                    asset_date = datetime.strptime(self.date[:7] + '-01', DF).date()
                # if we already have some previous validated entries, starting date isn't 1st January but last entry + method period
                if posted_depreciation_line_ids and posted_depreciation_line_ids[-1].depreciation_date:
                    last_depreciation_date = datetime.strptime(posted_depreciation_line_ids[-1].depreciation_date, DF).date()
                    depreciation_date = last_depreciation_date + relativedelta(months=+self.method_period)
                else:
                    depreciation_date = asset_date
            day = depreciation_date.day
            month = depreciation_date.month
            year = depreciation_date.year
            total_days = (year % 4) and 365 or 366

            undone_dotation_number = self._compute_board_undone_dotation_nb(depreciation_date, total_days)

            for x in range(len(posted_depreciation_line_ids), undone_dotation_number):
                sequence = x + 1
                amount = self._compute_board_amount(sequence, residual_amount, amount_to_depr, undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date)
                amount = self.currency_id.round(amount)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount
                vals = {
                    'amount': amount,
                    'asset_id': self.id,
                    'sequence': sequence,
                    'name': (self.code or '') + ' / ' + str(sequence) + ' / ' + depreciation_date.strftime('%d-%b-%Y'),
                    'remaining_value': residual_amount,
                    'depreciated_value': self.value - (self.salvage_value + residual_amount),
                    'depreciation_date': depreciation_date.strftime(DF),
                    'depreciation_date_org': depreciation_date.strftime(DF),
                }
                commands.append((0, False, vals))
                # Considering Depr. Period as months
                depreciation_date = date(year, month, day) + relativedelta(months=+self.method_period)
                day = depreciation_date.day
                month = depreciation_date.month
                year = depreciation_date.year

        self.write({'depreciation_line_ids': commands})

        return True

    @api.multi
    def revaluation(self, adjustment_value):
        if adjustment_value:
            self.value += adjustment_value
            if self.currency_id.is_zero(self.value_residual):
                self.state = 'close'
            else:
                self.state = 'open'
                self.compute_depreciation_board()

