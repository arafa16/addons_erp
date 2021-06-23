from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedProductTemplate(models.Model):
    _inherit = 'product.template'

    ww = 4

    @api.multi
    def write(self, vals):
        cc = vals.get('list_price',False)
        if cc != False:
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Sales Price dirubah dari "+str(self.list_price)+" menjadi "+str(cc)+" oleh <i>("+getusrs.email+")</i></b>")
        return super(EnhancedProductTemplate,self).write(vals)