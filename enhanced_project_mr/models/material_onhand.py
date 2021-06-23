from odoo import models, fields, api

class EnhancedmaterialOnhand(models.Model):
    _name = 'em.onhand'
    
    barang_id = fields.Many2one(
        comodel_name='product.product', 
        string='Product', 
        required=True)
    quantity = fields.Integer(string='Quantity')
    ret = fields.Integer(string='Return')
    ret_pros = fields.Integer(string='Return Proses')
    task_idx = fields.Many2one('project.task', string='Project Task')
    _sql_constraints = [('unique_product_own_list', 'unique(barang_id,task_idx)', 'Error! Multiple Produk pada Task yang sama!')]