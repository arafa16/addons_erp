from odoo import models, fields, api

class MaterialReturnProducts(models.Model):
    _name = 'em.return.products'

    barang_id = fields.Many2one(
        comodel_name='product.product', 
        string='Product', 
        required=True)
    ret_pros = fields.Integer(string='Return Proses')
    ret_done = fields.Integer(string='Return Done')
    ret_id = fields.Many2one('em.return', string='Return id', ondelete='cascade')