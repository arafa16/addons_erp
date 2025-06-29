from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseRequestBidding(models.Model):
    _inherit = 'sprogroup.purchase.request'

    nomor_bidding = fields.Many2one('purchase.requisition', string='Nomor Bidding')
    nomor_po_m2o = fields.Many2many(comodel_name='purchase.order', string='PO Numbers')
    
    @api.multi
    def back_to_buyer(self):
        if self.eksekutor.id == self._uid:
            self.state = 'leader_approved'
            self.isDispatch = False
        else:
            raise UserError("You don't have access to set RfQ")  

    @api.multi
    def make_bidding(self):
        if self.eksekutor.id == self._uid:
            isi = {}
            baris = []
            for br in self.line_ids:
                datake = []
                datake.append(0)
                datake.append('virtual_200'+str(self.id))
                kolom = {}
                kolom['price_unit'] = br.cost_product
                kolom['product_id'] = br.product_id.id
                kolom['product_qty'] = br.product_qty
                kolom['product_uom_id'] = br.product_id.uom_id.id
                kolom['schedule_date'] = br.date_required
                datake.append(kolom)
                baris.append(datake)
            aa = self.env['res.users'].browse(self._uid)
            isi['company_id'] = aa.company_id.id
            isi['line_ids'] = baris
            nama_baru = self.env['ir.sequence'].next_by_code('purchase.order.requisition')
            isi['name'] = nama_baru
            isi['picking_type_id'] = 1
            isi['state'] = 'draft'
            isi['type_id'] = 2
            isi['origin'] = self.name + ' ('+self.namex+')'
            isi['user_id'] = self._uid
            isi['nomor_pr'] = self.id
            isi['schedule_date'] = self.end_start
            tender = self.env['purchase.requisition'].create(isi)
            self.nomor_bidding = tender.id
        else:
            raise UserError("You don't have access to set RfQ")


class SprogroupPurchaseRequestLine(models.Model):
    _inherit = "sprogroup.purchase.request.line"

    nomor_bidding = fields.Many2one('purchase.requisition', string='Nomor Bidding', related='request_id.nomor_bidding')
