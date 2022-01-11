# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class AssetBalanceReportWizard(models.TransientModel):
    _name = "asset.balance.report.wizard"
    _description = "Asset Balance Report Wizard"

    year = fields.Char('Year', required=True, default=lambda self: fields.Date.from_string(fields.Date.today()).year)
    # category_ids = fields.Many2many('account.asset.category', string='Asset Categories')

    @api.multi
    def show_data(self):
        self.ensure_one()
        view_id = self.env.ref('account_asset_kopkarla.asset_balance_report_tree').id
        return {'type': 'ir.actions.act_window',
                'name': _('Asset Balance %s' % self.year),
                'res_model': 'asset.balance.report',
                'target': 'self',
                'view_mode': 'tree',
                # 'res_id': company.id,
                'views': [[view_id, 'tree']],
                'context': {'year': self.year},
        }
