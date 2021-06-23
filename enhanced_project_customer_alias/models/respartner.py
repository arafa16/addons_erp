from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedResPartner(models.Model):
    _inherit = 'res.partner'
    singkatan = fields.Char(string='Operation Alias')