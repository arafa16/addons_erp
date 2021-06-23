from odoo import models, fields, api, _
from odoo.exceptions import UserError

class HrEmployeeInherit(models.Model):
    _inherit = 'hr.employee'

    otoritas_purchase = fields.Many2many(comodel_name='tabel.ttd.purhchase', string='Purchase Authority')
    checkerPO = fields.Boolean(string='PO Checker')
    

    