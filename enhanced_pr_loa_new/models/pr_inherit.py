from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseReqeustLOAInherit(models.Model):
    _inherit = 'sprogroup.purchase.request'
    
    ww = 4