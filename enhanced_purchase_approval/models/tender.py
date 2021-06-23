from odoo import models, fields, api, _
from odoo.exceptions import UserError

class InheritTenderforDone(models.Model):
    _inherit = 'purchase.requisition'

    @api.multi
    def action_done(self):
        if any(purchase_order.state in ['draft', 'sent', 'to approve','assmancheck','requestloa','loaconfirmed'] for purchase_order in self.mapped('purchase_ids')):
            raise UserError(_('You have to cancel or validate every RfQ before closing the purchase requisition.'))
        self.write({'state': 'done'})
    