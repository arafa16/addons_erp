from odoo import api, fields, models

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    cost_center_id = fields.Many2one("cost.center", string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade")
