from odoo import models, fields, api, _
from odoo.exceptions import UserError

class DepartemenEnhanced(models.Model):
    _inherit = 'hr.department' 
    adadiSO = fields.Boolean(string='On Quotation') 
    kodeSO = fields.Char(string='Code On Quotation')

    def trigger_user(self):
        ww = 4
        gettask = self.env['project.task'].search([('id','>',0)])
        for tsk in gettask:
            temp = tsk.description
            tsk.write({'data_teknis':temp})
        # getEmployee = self.env['hr.employee'].search([('id','>',1)])
        # for emp in getEmployee:
        #     getuser = self.env['res.users'].search([('login','=',emp.work_email)])
        #     if getuser.id != False:
        #         if emp.user_id.id == False:
        #             emp.write({'user_id':getuser.id})
        # ww = 4
        # dd = self.env['res.users'].search([('id','>',1)])
        # for usr in dd:
        #     if usr.email == False:
        #         usr.email = usr.login
        # ww = 4
        # getuser = self.env['res.users'].search([('id','>',1)])
        # getaction = self.env['ir.actions.actions'].search([('name','=','My Dashboard')])
        # for usr in getuser:
        #     usr.write({'action_id':getaction.id})
