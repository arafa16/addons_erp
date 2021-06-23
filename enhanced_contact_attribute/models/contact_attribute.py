from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ContactAttribute(models.Model):
    _inherit = 'res.partner'
    active = fields.Boolean(default=True,track_visibility='onchange')
    tdp = fields.Char(string='TDP/NIB')
    tdp_berkalu = fields.Date(string='TDP Expired')
    siup = fields.Char(string='SIUP')
    siup_berkalu = fields.Date(string='SIUP Expired')
    pkp = fields.Boolean(string='PKP')
    pkp_number =fields.Char(string='Nomor PKP')
    jumlah_credit_limit = fields.Integer(string='Credit Limit',compute='setToBadge',track_visibility='onchange')
    openInv = fields.Float(string='Open Invoice',store=False)
    # singkatan = fields.Char(string='Operation Alias')
    # fax_numx = fields.Char(string='Fax Number')
    
    @api.multi
    def press_creditlimit(self):
        qqq = 3
    
    @api.multi
    def setToBadge(self):
        for doc in self:
            doc.jumlah_credit_limit = doc.credit_limit
            doc.openInv = doc.total_invoiced
    