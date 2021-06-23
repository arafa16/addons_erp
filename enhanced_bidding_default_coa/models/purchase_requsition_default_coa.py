from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedPurchaseRequsitionDefaultCoA(models.Model):
    _inherit = 'purchase.requisition'

    related_coa = fields.Many2one('account.account', related='nomor_pr.coannya', string='Related CoA')

    ww = 4