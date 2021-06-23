from odoo import models, fields, api

class MaterialRekuestLine(models.Model):
    _name = 'material.rekuest.line'
    
    produk_id = fields.Many2one('product.product', string='Product')
    stock_location = fields.Many2one('stock.location', string='Stock Location')
    stockAvailable = fields.Integer(string='Stock Avaialable', compute='get_stock')
    permintaan = fields.Integer(string='Jumlah Qty')
    opration_id = fields.Many2one('stock.picking', string='Operation Code')
    permintaan_done = fields.Integer(string='Qty Done')
    mr_id = fields.Many2one('material.rekuest', 'Material Request')

    @api.depends('produk_id', 'stock_location')
    def get_stock(self):
        getstock = self.env['stock.quant'].search(['&',('product_id','=',self.produk_id.id),('location_id','=',self.stock_location.id)])
        if getstock.id != False:
            self.stockAvailable = getstock.quantity
        else:
            self.stockAvailable = 0
    