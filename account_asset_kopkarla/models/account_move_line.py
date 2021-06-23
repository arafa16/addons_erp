# -*- coding: utf-8 -*-
# (C) 2013 Smile (<http://www.smile.fr>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    asset_id = fields.Many2one(
        'account.asset.asset', 'Asset',
        readonly=True, ondelete='restrict')
    depre_lines = fields.One2many('account.move.line.depreciation', 'move_line_id', 'Asset')


class AccountMoveLineDepre(models.Model):
    _name = 'account.move.line.depreciation'
    _description = "Journal Asset Depreciation"

    name = fields.Char(string="Label")
    move_line_id = fields.Many2one('account.move.line', 'Move Line', ondelete='cascade')
    asset_id = fields.Many2one('account.asset.asset', 'Asset', readonly=True, ondelete='restrict')
    debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    # balance = fields.Monetary(compute='_store_balance', store=True, currency_field='company_currency_id')
    amount_currency = fields.Monetary(default=0.0)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency")
    currency_id = fields.Many2one('res.currency', string='Currency')
    account_id = fields.Many2one('account.account', string='Account', ondelete="cascade")
    move_id = fields.Many2one('account.move', string='Journal Entry', ondelete="cascade", related="move_line_id.move_id", store=True)
    date = fields.Date(related='move_line_id.date', string='Date', store=True)  # related is required
    cost_center_id = fields.Many2one("cost.center", string="Cost Center",)
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    company_id = fields.Many2one('res.company', related='account_id.company_id', string='Company', store=True, readonly=True)
    state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], string='Status', related="move_id.state", store=True)
