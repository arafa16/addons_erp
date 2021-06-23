from odoo import models, fields, api, _
from odoo.exceptions import UserError

class InheritPurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    template_tnc = fields.Many2one('tabel.tnc.purchase', string='Template')

    @api.onchange('template_tnc')
    def set_note(self):
        if self.template_tnc.id == False:
            self.notes = ''
        else:    
            self.notes = self.template_tnc.description
    