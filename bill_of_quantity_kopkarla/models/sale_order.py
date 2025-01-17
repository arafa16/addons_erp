from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('opportunity_id')
    def _onchange_opportunity_id(self):
        if self.opportunity_id:
            self.update(self.opportunity_id.quotation_values())
