from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    boq_id = fields.Many2one('bill.quantity', 'Bill of Quantity', compute='_get_boq_id', store=True)

    @api.depends('opportunity_id', 'opportunity_id.boq_ids')
    def _get_boq_id(self):
        for sale in self:
            boq_id = False
            if sale.opportunity_id:
                if sale.opportunity_id.boq_ids:
                    boq = sale.opportunity_id.boq_ids.filtered(lambda b: b.state == 'posted')
                    if boq:
                        boq_id = boq[0].id
            sale.boq_id = boq_id

    @api.onchange('opportunity_id')
    def _onchange_opportunity_id(self):
        if self.opportunity_id:
            self.update(self.opportunity_id.quotation_values())

    def action_view_boq(self):
        action = {
            'name': _('Bill Of Quantity'),
            'type': 'ir.actions.act_window',
            'res_model': 'bill.quantity',
            'target': 'current',
        }
        action['res_id'] = self.boq_id.id
        action['view_mode'] = 'form'
        return action