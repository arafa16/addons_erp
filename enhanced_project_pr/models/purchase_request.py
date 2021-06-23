from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectPrInheritPurchaseRequest(models.Model):
    _inherit = 'sprogroup.purchase.request'

    @api.model
    def create(self, vals):
        request = super(ProjectPrInheritPurchaseRequest, self).create(vals)
        if request.pjtask.id != False:
            pjtask = request.pjtask.id
            tsk = self.env['project.task'].browse(pjtask)
            tskm2m = tsk.purchase_req_m2m
            isi1 = []
            for asal in tskm2m:
                isi1.append(asal.id)
            isi1.append(request.id)
            isi2 = []
            isi2.append(6)
            isi2.append(False)
            isi2.append(isi1)
            updateisi = []
            updateisi.append(isi2)
            tsk.write({'purchase_req':request.id,'purchase_req_m2m':updateisi})
        return request
    