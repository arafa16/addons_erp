from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import random

class EmRequest(models.Model):
    _name = 'em.request'

    name = fields.Char(string='Deskripsi MR')
    tanggal = fields.Date(string='Tanggal Permintaan',default=fields.Date.today())
    material_ids = fields.One2many('em.request.product', 'mr_id', string='Daftar Material')
    task_idx = fields.Many2one('project.task', string='Project Task')
    stat = fields.Selection([("draft","Draft"),("close","Proses")], string='Status',default=lambda self: 'draft')
    picking_id = fields.Many2one('stock.picking', 'Picking', compute='_get_picking_id')

    def _get_picking_id(self):
        for mr in self:
            mr.picking_id = self.env['stock.picking'].sudo().search([('name', '=', mr.material_ids[0].moveopr)]).id

    @api.multi
    def set_proses(self):
        # cek gudang cutomer
        gudcust = self.env['stock.location'].search([('usage','=','customer')])
        if len(gudcust) > 0:
            linex = self.material_ids
            # gruping gudang
            gudang = []
            for li in linex:
                sudahada = False
                for dd in gudang:
                    if dd == li.gudang_pengambilan.id:
                        sudahada = True
                if sudahada == False:
                    gudang.append(li.gudang_pengambilan.id)
            now = datetime.now()
            curtime = now.strftime("%Y-%m-%d %H:%M:%S")
            for gud in gudang:
                stloc = self.env['stock.location'].browse(gud)
                wh = stloc.get_warehouse().id
                oprtipe = self.env['stock.picking.type'].search([('warehouse_id','=',wh),('code','=','outgoing')])
                if len(oprtipe) > 0:
                    isian = {}
                    isian['company_id'] = stloc.company_id.id
                    isian['is_locked'] = True
                    isian['location_dest_id'] = gudcust[0].id
                    isian['location_id'] = gud
                    isian['move_type'] = 'direct'
                    isian['note'] = self.name
                    isian['origin'] = self.task_idx.name
                    isian['owner_id'] = False
                    isian['partner_id'] = self.task_idx.related_cust.id
                    isian['picking_type_id'] = oprtipe[0].id
                    isian['priority'] = '1'
                    isian['idmr'] = self.id
                    isian['idtask'] = self.task_idx.id
                    isian['mr_responsible'] = self.create_uid.id
                    isian['move_lines'] = []
                    for la in linex:
                        if la.gudang_pengambilan.id == gud:
                            baris = []
                            baris.append(0)
                            baris.append(la.id)
                            isiapend = {}
                            isiapend['additional'] = False
                            isiapend['date_expected'] = curtime
                            isiapend['location_dest_id'] = gudcust[0].id
                            isiapend['location_id'] = gud
                            isiapend['picking_type_id'] = oprtipe[0].id
                            isiapend['name'] = la.barang_id.name
                            isiapend['product_id'] = la.barang_id.id
                            isiapend['product_uom'] = la.barang_id.uom_id.id
                            isiapend['product_uom_qty'] = la.permintaan
                            isiapend['state'] = 'draft'
                            baris.append(isiapend)
                            isian['move_lines'].append(baris)
                            la.statx = 'progress'
                    ww = 6
                    # create inventory transfer
                    tt = self.env['stock.picking'].create(isian)
                    for lo in linex:
                        if lo.gudang_pengambilan.id == gud:
                            lo.moveopr = tt.display_name
                    # update product stock picking
                else:
                    raise UserError('Tidak ada Operation Type Delivery Order')
            self.stat = 'close'
            ww = 4
        else:
            raise UserError('Gudang Customer Belum di set')
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def process_wizard(self):
        ww = 3

    @api.model
    def create(self, vals):
       aa = self._context.get('id_conx',False)
       if aa != False:
           vals['task_idx'] = aa
       return super(EmRequest, self).create(vals)
