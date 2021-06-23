# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import *

ASSET_CLASSES = [
    ('tangible', 'Tangible'),
    ('intangible', 'Intangible'),
]

class AccountAssetCategory(models.Model):
    _inherit = "account.asset.category"

    account_depreciation_id = fields.Many2one('account.account', string='Depreciation Entries: Asset Account', required=False, domain=[('internal_type','=','other'), ('deprecated', '=', False)], help="Account used in the depreciation entries, to decrease the asset value.")
    account_depreciation_expense_id = fields.Many2one('account.account', string='Depreciation Entries: Expense Account', required=False, domain=[('internal_type','=','other'), ('deprecated', '=', False)], oldname='account_income_recognition_id', help="Account used in the periodical entries, to record a part of the asset as expense.")
    account_profit_id = fields.Many2one(comodel_name="account.account", string="Profit Account",)
    account_loss_id = fields.Many2one(comodel_name="account.account", string="Loss Account",)
    journal_id = fields.Many2one('account.journal', string='Journal Depre.', required=False)
    journal_acq_id = fields.Many2one('account.journal', string='Journal Acq.', required=False)
    journal_disp_id = fields.Many2one('account.journal', string='Journal Disposal', required=False)
    journal_reclass_id = fields.Many2one('account.journal', string='Journal Reclass', required=False)
    journal_reval_id = fields.Many2one('account.journal', string='Journal Revaluation', required=False)
    asset_class = fields.Selection(ASSET_CLASSES, required=True)
    asset_in_progress = fields.Boolean()
    # sequence_reclass_id = fields.Many2one('ir.sequence', string='Reclass IDs Sequence', readonly=False,
    #                       help="This sequence is automatically created by Odoo but you can change it "
    #                            "to customize the reference numbers of your orders.", copy=False)

    @api.onchange('asset_in_progress')
    def _onchange_asset_in_progress(self):
        if self.asset_in_progress:
            self.method_number = 0
            self.method_period = 0
        #     self.accounting_method = 'none'
        #     self.fiscal_method = 'none'
        # else:
        #     self.accounting_method = 'linear'
        #     self.fiscal_method = 'linear'