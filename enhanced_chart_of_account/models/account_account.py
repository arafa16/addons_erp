from odoo import models, fields, api, _
from odoo.exceptions import UserError

class InheritAccountAccount(models.Model):
    _inherit = 'account.account'
    parent_id = fields.Many2one('account.account', 'Parent Account')
    child_ids = fields.One2many('account.account', 'parent_id', 'Children')

    @api.onchange('parent_id')
    def get_price(self):
        ww = 4
        # employ = self.env['hr.employee'].search([('id','>',0)])
        # for idx in employ:
        #     getuser = self.env['res.users'].search([('login','=',idx.work_email)])
        #     if getuser.id != False:
        #         idx.user_id = getuser.id
    

    