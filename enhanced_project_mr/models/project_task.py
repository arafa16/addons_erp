from odoo import models, fields, api, _
from odoo.exceptions import UserError

class NamaModel(models.Model):
    _inherit = 'project.task'
    mr_ids = fields.One2many('em.request', 'task_idx', string='Material Request')
    related_mr = fields.Boolean(related='stage_id.material_req')
    # onhand = fields.One2many('enhanced.material.request.product', 'taskid', string='On Hand Material', domain=[('statx', 'in', ['parsial','done'])])
    barangown = fields.One2many('em.onhand', 'task_idx', string='Barang Own')

    related_ret = fields.Boolean(related='stage_id.material_ret')
    return_ids = fields.One2many('em.return', 'task_idx', string='Return Material', ondelete='cascade')
    cost_center_id = fields.Many2one("cost.center", string='Cost Center')

    @api.multi
    def write(self, values):
        xx = values.get('mr_ids',False)
        if xx != False:
            nn = 0
            for yy in xx:
                if yy[0] == 2:
                    getc = self.env['em.request'].browse(yy[1])
                    if getc.stat != 'draft':
                        values['mr_ids'][nn][0] = 4
                nn = nn + 1
        
        zz = values.get('return_ids',False)
        if zz != False:
            nn = 0
            for yy in zz:
                if yy[0] == 2:
                    getc = self.env['em.return'].browse(yy[1])
                    if getc.stat != 'draft':
                        values['return_ids'][nn][0] = 4
                nn = nn + 1
                
        return super(NamaModel, self).write(values)

    @api.multi
    def form_return(self):
        aa = self.env['em.return'].search([('task_idx','=',self.id)])
        donesemua = True
        for bb in aa:
            ww = 4
            if bb.stat != 'done':
                donesemua = False
        if donesemua == True:
            ww = 4
            imd = self.env['ir.model.data']
            listx = imd.xmlid_to_res_id('enhanced_project_mr.em_return_wizard_form')
            return {
                    'type': 'ir.actions.act_window',
                    'name': 'Form Material Return',
                    'res_model': 'em.return',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'views': [[listx,'form']],
                    'context': {'id_conx':self.id},
                    'target': 'new',
                    'view_id': listx
                }
        else:
            raise UserError('Masih terdapat Form Pengembalian yang belum diproses')