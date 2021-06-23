from odoo import api, fields, models, _

class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="restrict", required=True)
