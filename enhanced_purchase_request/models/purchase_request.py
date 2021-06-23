from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseReqeustInherit(models.Model):
    _inherit = 'sprogroup.purchase.request'

    amount_total = fields.Float(compute='compute_total', string='Total', store=False)
    
    def print_purchase_request_dokumen(self):
        for doc in self:
            ww = doc
        return self.env.ref('enhanced_purchase_request.action_report_purchase_request').report_action(ww)
    
    @api.multi
    @api.depends('line_ids')
    def compute_total(self):
        for doc in self:
            amount_total = 0
            for baris in doc.line_ids:
                amount_temp = baris.product_qty *  baris.cost_product
                amount_total = amount_total +  amount_temp
            doc.amount_total = amount_total
    
    