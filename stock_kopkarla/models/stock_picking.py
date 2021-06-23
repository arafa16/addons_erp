from odoo import api, fields, models

class Picking(models.Model):
    _inherit = "stock.picking"

    cost_center_id = fields.Many2one("cost.center", string='Cost Center')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account', ondelete="cascade")

    @api.onchange('analytic_account_id')
    def set_analytic_account(self):
        for line in self.move_lines:
            line.analytic_account_id = self.analytic_account_id.id

    @api.onchange('cost_center_id')
    def set_cost_center(self):
        for line in self.move_lines:
            line.cost_center_id = self.cost_center_id.id
