# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAssetReclass(models.TransientModel):
    _name = 'account.asset.reclass'
    _description = 'Reclass Asset'

    name = fields.Text(string='Reason', required=True)
    method = fields.Selection([('category', 'Change Category'), ('asset', 'Reclass Asset')], required=True, default='category')
    asset_id = fields.Many2one('account.asset.asset', string='Asset', readonly=True)
    category_id = fields.Many2one('account.asset.category', string='Category', readonly=True)
    new_asset_id = fields.Many2one('account.asset.asset', string='New Asset')
    new_category_id = fields.Many2one('account.asset.category', string='New Category', required=False, change_default=True, readonly=False, states={'draft': [('readonly', False)]})
    date = fields.Date(string='Date', help="Leave empty to use the current date")

    # method_number = fields.Integer(string='Number of Depreciations', required=True)
    # method_period = fields.Integer(string='Period Length')
    # method_end = fields.Date(string='Ending date')
    # asset_method_time = fields.Char(compute='_get_asset_method_time', string='Asset Method Time', readonly=True)

    # @api.one
    # def _get_asset_method_time(self):
    #     if self.env.context.get('active_id'):
    #         asset = self.env['account.asset.asset'].browse(self.env.context.get('active_id'))
    #         self.asset_method_time = asset.method_time
    #
    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     result = super(AssetModify, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
    #     asset_id = self.env.context.get('active_id')
    #     active_model = self.env.context.get('active_model')
    #     if active_model == 'account.asset.asset' and asset_id:
    #         asset = self.env['account.asset.asset'].browse(asset_id)
    #         doc = etree.XML(result['arch'])
    #         if asset.method_time == 'number' and doc.xpath("//field[@name='method_end']"):
    #             node = doc.xpath("//field[@name='method_end']")[0]
    #             node.set('invisible', '1')
    #             setup_modifiers(node, result['fields']['method_end'])
    #         elif asset.method_time == 'end' and doc.xpath("//field[@name='method_number']"):
    #             node = doc.xpath("//field[@name='method_number']")[0]
    #             node.set('invisible', '1')
    #             setup_modifiers(node, result['fields']['method_number'])
    #         result['arch'] = etree.tostring(doc, encoding='unicode')
    #     return result

    @api.model
    def default_get(self, fields):
        res = super(AccountAssetReclass, self).default_get(fields)
        asset_id = self.env.context.get('active_id')
        asset = self.env['account.asset.asset'].browse(asset_id)
        if 'asset_id' in fields:
            res.update({'asset_id': asset.id})
        if 'category_id' in fields:
            res.update({'category_id': asset.category_id.id})
        # if 'method_number' in fields and asset.method_time == 'number':
        #     res.update({'method_number': asset.method_number})
        # if 'method_period' in fields:
        #     res.update({'method_period': asset.method_period})
        # if 'method_end' in fields and asset.method_time == 'end':
        #     res.update({'method_end': asset.method_end})
        # if self.env.context.get('active_id'):
        #     active_asset = self.env['account.asset.asset'].browse(self.env.context.get('active_id'))
        #     res['asset_method_time'] = active_asset.method_time
        return res

    @api.multi
    def reclass(self):
        asset_id = self.env.context.get('active_id', False)
        asset = self.env['account.asset.asset'].browse(asset_id)
        new_category = self.new_category_id
        if asset.category_id.id == new_category.id:
            raise UserError(_('You cannot reclass to same category.'))
        asset.reclass(False, asset.category_id, new_category, self.date, self.name)
        old_values = {
            'category_id': asset.category_id.id,
            'method_number': asset.method_number,
            'method_period': asset.method_period,
        }
        asset_vals = {
            'category_id': self.new_category_id.id,
            'method_number': new_category.method_number,
            'method_period': new_category.method_period,
        }
        asset.write(asset_vals)
        asset.compute_depreciation_board()
        tracked_fields = self.env['account.asset.asset'].fields_get(['category', 'method_number', 'method_period'])
        changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
        if changes:
            asset.message_post(subject=_('Depreciation board modified'), body=self.name, tracking_value_ids=tracking_value_ids)
        return {'type': 'ir.actions.act_window_close'}
