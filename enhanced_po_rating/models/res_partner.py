from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime

class ResPartner(models.Model):
    _inherit = 'res.partner'
    ratingavg = fields.Float(string='Rating Sum',compute='hitug_avg')
    periode = fields.Many2one('res.partner.periode', string='Periode')
    faks_num = fields.Char(string='Fax Number')
    ww = 4

    @api.multi
    @api.depends('periode')
    def hitug_avg(self):
        ff = self._context.get('params',False)
        if ff == False:
            ee = 4
        else:
            idg = ff.get('id','')
            if idg == '':
                idf = False
            else:
                idf = idg
            if idf != False:
                dd = self.env['purchase.order'].search([('partner_id','=',idg),('date_order','>=',self.periode.tanggal1),('date_order','<=',self.periode.tanggal2),('ratingx','>',0)])
                if len(dd) ==0:
                    avgx = 0
                else:
                    avgx = sum(dd.mapped('ratingx')) / len(dd)
                self.ratingavg = avgx