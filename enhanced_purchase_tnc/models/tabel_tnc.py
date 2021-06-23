from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TabelTncPurchase(models.Model):
    _name = 'tabel.tnc.purchase'

    name = fields.Char(string='Template Term & Condition')
    description = fields.Text(string='Deskripsi')