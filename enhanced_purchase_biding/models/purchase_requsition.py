from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedPurchaseRequsition(models.Model):
    _inherit = 'purchase.requisition'

    nomor_pr = fields.Many2one('sprogroup.purchase.request', string='Nomor PR')

    ww = 4
    @api.multi
    def clear_agrement(self):
        self.state = 'cancel'
        getpr = self.nomor_pr
        getpr.nomor_bidding = False

    def set_rollback(self):
        self.write({'state':'open'})
    