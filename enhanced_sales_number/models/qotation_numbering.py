from odoo import models, fields, api, _
from odoo.exceptions import UserError

class QotationAttribute(models.Model):
    _inherit = 'sale.order'
    namex = fields.Char(string='Kode Qotation',)

    @api.model
    def create(self, vals):
        ii = 1
        ketemu = False
        sPrev = ''
        while ketemu == False:
            aa = self.env['ir.sequence'].browse(ii)
            if aa.code == "sale.order":
                ketemu = True
                sPrev = aa.prefix
            ii = ii + 1
            if ii == 50:
                ketemu = True
        nmrdept = vals['so_bagian']
        nextCode = self.env['ir.sequence'].next_by_code('sale.order')
        nextCode = nextCode+""
        bb = nextCode.replace(sPrev,'')
        nmrbaru = sPrev+''+self.env['hr.department'].browse(nmrdept).kodeSO+'/'+bb
        vals['name'] = nmrbaru
        return super(QotationAttribute, self).create(vals)