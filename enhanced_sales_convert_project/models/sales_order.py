from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SalesOrderESCP(models.Model):
    _inherit = 'sale.order'

    task_id = fields.Many2one('project.task', "Task", readonly=False, copy=False, index=True, tracking=True)
    project_id = fields.Many2one('project.project', "Project", related='task_id.project_id', store=True, copy=False, index=True, tracking=True)
    kanbanbaru = fields.Selection(selection=[('A', 'Not Started'),('B', 'On Progress'),('C', 'Stop Clock'),('D', 'Done'),('E', 'Cancel')],related='task_id.kanban_baru',string='Status Pelaksanaan')

    @api.multi
    def task_relation(self):
        self.ensure_one()
        return {
            'name': _("Related Task"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.task',
            'view_id': False,
            'res_id': self.task_id.id,
            'type': 'ir.actions.act_window',
        }
    
    def task_spk_invoice_reject(self):
        self.ensure_one()
        if self.task_id.stage_id.ready_invoice == True and self.task_id.kanban_baru == 'D':
            self.task_id.write({'kanban_baru':'B'})
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.task_id.message_post(body="Document Rejected By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")

    

    @api.multi
    def convert_to_project(self):
        projid = 0
        cekProj = self.env['project.project'].search([('partner_id','=',self.partner_shipping_id.id),('j_project','=',self.proj_type.id),('nojar','=',self.nojar)])
        if len(cekProj) > 0:
            projid = cekProj[0].id
        else:
            if self.nojar == False or self.nojar == "":
                namaProj = self.proj_type.name+" "+self.partner_shipping_id.name
            else:
                namaProj = self.proj_type.name+" "+self.partner_shipping_id.name+" Nojar. "+self.nojar

            isiProject = {
                'active': True, 
                'alias_contact': 'everyone', 
                'alias_id': False, 
                'alias_name': False, 
                'analytic_account_id': False,
                'label_tasks': 'Tasks',
                'name': namaProj,
                'partner_id': self.partner_shipping_id.id,
                'privacy_visibility':'employees',
                'resource_calendar_id': False,
                'sequence': 10,
                'subtask_project_id': False,
                'user_id': self._uid,
                'type_ids': False,
                'j_project':self.proj_type.id,
                'nojar':self.nojar
            }
            projo = self.env['project.project'].create(isiProject)
            projid = projo.id

        bb = self.env['project.task.type'].search([('jenis_pek','in',self.pek_type.id)])
        stageid = False
        stageproj = []
        ke7 = 0
        for cc in bb:
            if ke7 == 0:
                stageid = cc.id
            ke7 = ke7 + 1
            adac = False
            for cfr in cc.project_ids:
                if cfr.id == projid:
                    adac = True
            if adac == False:
                valsa = {}
                valsa['project_ids'] = []
                keong = []
                keong.append(4)
                keong.append(projid)
                valsa['project_ids'].append(keong)
                cc.write(valsa)
        
        tagid = []
        isitag = []
        isitag.append(6)
        isitag.append(False)
        isi2 = []
        isitag.append(isi2)
        tagid.append(isitag)
        if self.nojar == False or self.nojar == "":
            namaTask = self.pek_type.name+" "+self.proj_type.name+" "+self.partner_shipping_id.name
        else:
            namaTask = self.pek_type.name+" "+self.proj_type.name+" "+self.partner_shipping_id.name+" Nojar. "+self.nojar                
        isiTask = {
            'active': True,
            'company_id': self.company_id.id,
            'description': '<p><br></p>',
            'kanban_state': 'normal',
            'name': namaTask,
            'parent_id': False,
            'partner_id': self.partner_shipping_id.id,
            'priority': '0',
            'project_id': projid,
            'sale_order_id': self.id,
            'stage_id': stageid,
            'user_id': self._uid,
            'kanban_baru': 'A'
        }
        self.task_id = self.env['project.task'].create(isiTask)