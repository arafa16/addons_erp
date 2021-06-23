from odoo import models, fields, api, exceptions, _

class EMRequestProduct(models.Model):
    _name = 'em.request.product'

    mr_id = fields.Many2one('em.request', string='Material Request')
    taskid = fields.Many2one('project.task', related="mr_id.task_idx", string='Task ID')
    barang_id = fields.Many2one(
        comodel_name='product.product', 
        string='Product', 
        required=True)
    gudang_pengambilan = fields.Many2one(
        comodel_name='stock.location',
        string='Gudang',
        required=True,
        index=True)
    permintaan = fields.Integer(string='Permintaan')
    tersedia = fields.Char(string='Check Stok')
    direserve = fields.Integer(string='Reserve')
    dikirim = fields.Integer(string='Diterima')
    dikembalikan = fields.Integer(string='Dikembalikan')
    moveopr = fields.Char(string='Inventory Code')
    statx = fields.Selection([("draft","Draft"),("progress","Progress"),("parsial","Parsial Deliver"),("done","Done")], string='Status',default=lambda self: 'draft')
    _sql_constraints = [('unique_product_list', 'unique(barang_id,gudang_pengambilan,mr_id)', 'Error! Multiple Produk pada Gudang yang sama!')]

    @api.multi
    @api.onchange('barang_id','gudang_pengambilan')
    def get_stock(self):
        id_gudang = self.gudang_pengambilan.id
        id_stoks = self.barang_id.stock_quant_ids
        self.tersedia = ''
        ada = False
        tersedia = 0
        for ids in id_stoks:
            if id_gudang != False and ids.location_id.id == id_gudang:
                tersedia = tersedia + ids.quantity
                ada = True
        if ada == False:
            self.tersedia = 'Tidak ada Stok'
        else:
            self.tersedia = str(tersedia)