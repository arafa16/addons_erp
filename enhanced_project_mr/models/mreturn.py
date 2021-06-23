from odoo import models, fields, api
from odoo.exceptions import UserError

class EnhancedMaterialReturn(models.Model):
    _name = 'em.return'

    name = fields.Char(string='Dokumen Return')
    tanggal = fields.Date(string='Tgl. Pengembalian',default=fields.Date.today())
    kode_move = fields.Char(string='Warehouse Proses')
    task_idx = fields.Many2one('project.task', string='Project Task',default=lambda self: self._context.get('id_conx',False))
    material_ids = fields.One2many('em.onhand', 'ret_id', string='Daftar Material', related="task_idx.barangown")
    return_ids = fields.One2many('em.return.products', 'ret_id', string='Daftar Material Return', ondelete='cascade')
    stat = fields.Selection([("draft","Draft"),("close","Proses"),("done","Done")], string='Status',default=lambda self: 'draft')
    gudang_return = fields.Many2one(
        comodel_name='stock.location',
        string='Gudang',
        required=True,
        index=True)

    @api.multi
    def set_proses(self):
        if self.env.uid != self.task_idx.user_id.id:
            raise UserError('You Dont have acess to approve this document')
        else:
            if len(self.return_ids) > 0:
                boleh = True
                for line in self.return_ids:
                    getoh = self.env['em.onhand'].search([('barang_id','=',line.barang_id.id),('task_idx','=',self.task_idx.id)])
                    if len(getoh) > 0:
                        if getoh.quantity < (line.ret_pros + getoh.ret):
                            boleh = False
                    else:
                        boleh = False
                        raise UserError('Link tidak ditemukan')
                if boleh == True:
                    wh = self.gudang_return.get_warehouse().id
                    oprtipe = self.env['stock.picking.type'].search([('warehouse_id','=',wh),('code','=','incoming')])
                    gudvendor = self.env['stock.location'].search([('usage','=','supplier')])
                    if len(gudvendor) > 0:
                        if len(oprtipe) > 0:
                            isian = {}
                            isian['idreturn'] = self.id
                            isian['company_id'] = self.gudang_return.company_id.id
                            isian['is_locked'] = True
                            isian['location_dest_id'] = self.gudang_return.id
                            isian['location_id'] = gudvendor.id
                            isian['move_type'] = 'direct'
                            isian['note'] = self.task_idx.name
                            isian['origin'] = self.task_idx.sale_order_id.name
                            isian['owner_id'] = False
                            isian['partner_id'] = self.task_idx.partner_id.id
                            isian['picking_type_id'] = oprtipe[0].id
                            isian['priority'] = '1' 
                            isiline = []
                            for baris in self.return_ids:
                                isiappend = []
                                isiappend.append(0)
                                isiappend.append('virtual_200'+str(baris.id))
                                isibaris = {}
                                isibaris['location_id'] = gudvendor.id
                                isibaris['name'] = baris.barang_id.name
                                isibaris['picking_type_id'] = oprtipe[0].id
                                isibaris['product_id'] = baris.barang_id.id
                                isibaris['product_uom'] = baris.barang_id.uom_id.id
                                isibaris['product_uom_qty'] = baris.ret_pros
                                isibaris['state'] = 'draft'
                                isiappend.append(isibaris)
                                isiline.append(isiappend)
                            isian['move_lines'] = isiline
                            ww = 4
                            tt = self.env['stock.picking'].create(isian)
                            self.stat = 'close'
                            self.kode_move = tt.display_name
                            return {
                                'type': 'ir.actions.client',
                                'tag': 'reload',
                                }
                        else:
                            raise UserError('Proses Receiving belum di set di warehouse')
                    else:
                        raise UserError('Belum ada Gudang Vendor yang diset')
                else:
                    raise UserError('Nilai Pengembalian Lebih besar dari Material on Hand')
            else:
                raise UserError('Tidak ada Line yang diproses')

    @api.multi
    def process_return(self):
        ww = 3

    @api.model
    def create(self, vals):
        aa = self._context.get('id_conx',False)
        if aa != False:
           vals['task_idx'] = aa
        material = vals['material_ids']
        ff = super(EnhancedMaterialReturn, self).create(vals)
        for mat in material:
            if mat[0] == 1:
                if mat[2]['ret_pros'] > 0:
                    isi = {}
                    vv = self.env['em.onhand'].browse(mat[1])
                    isi['barang_id'] = vv.barang_id.id
                    isi['ret_pros'] = mat[2]['ret_pros']
                    isi['ret_id'] = ff.id
                    isi['ret_done'] = 0
                    self.env['em.return.products'].create(isi)
                    vv.ret_pros = 0
        return ff