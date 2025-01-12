from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectTaskPR(models.Model):
    _inherit = 'project.task'

    purchase_req = fields.Many2one('sprogroup.purchase.request', string='Purchase Request')
    purchase_req_m2m = fields.Many2many(comodel_name='sprogroup.purchase.request', string='Purchase Requests')

    # @api.multi
    def action_purchase_request(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Request',
            'res_model': 'sprogroup.purchase.request',
            'view_type': 'form',
            'context': {'default_pjtask' : self.id, "default_salesorder_id": self.sale_order_id.id, 'fromproject' : True},
            'view_mode': 'form',
            'target': 'current',
        }