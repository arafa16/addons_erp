from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class StockPickingEnhanced(models.Model):
    _inherit = 'stock.picking'

    ww = 4
    idmr = fields.Many2one('em.request', string='Material Request Id')
    idtask = fields.Many2one('project.task', string='Id Task')
    idreturn = fields.Many2one('em.return', string='Material Return Id')
    mr_responsible = fields.Many2one('res.users', string='Responsible')
    sopr = fields.Char(string='SO on PR', compute='setnamaso',)
    pr_no = fields.Char(string='PR', compute='setnamaso',)
    pr_date = fields.Date(string='PR Date', compute='setnamaso',)
    sopraddress = fields.Char(string='SO on PR Address',compute="setalamatso")
    isDirect = fields.Char(string='Inventory Process', compute='setdirecttocust',)
    prCreator = fields.Char(string='PR Requested By', compute='setPrOwner',)

    @api.depends()
    def setPrOwner(self):
        for doc in self:
            if doc.purchase_id.id != False:
                idpr = doc.purchase_id.requisition_id.nomor_pr.id
                if idpr != False:
                    doc.prCreator = doc.purchase_id.requisition_id.nomor_pr.requested_by.display_name

    @api.depends()
    def setnamaso(self):
        for doc in self:
            if doc.purchase_id.id != False:
                pr_id = doc.purchase_id.requisition_id.nomor_pr
                if pr_id != False:
                    doc.pr_no = pr_id.name
                    doc.pr_date = pr_id.date_start
                else:
                    doc.pr_id = 'Tidak ada PR'
                    doc.pr_date = False

                xx = doc.purchase_id.requisition_id.nomor_pr.salesorder_id.name
                if xx != False:
                    doc.sopr = xx 
                else:
                    doc.sopr = 'Tidak ada SO'

    @api.depends()
    def setalamatso(self):
        for doc in self:
            if doc.purchase_id.id != False:
                yy = doc.purchase_id.requisition_id.nomor_pr.salesorder_id.partner_shipping_id.display_name
                if yy != False:
                    doc.sopraddress = yy 
                else:
                    doc.sopraddress = ''

    @api.depends()
    def setdirecttocust(self):
        for doc in self:
            if doc.purchase_id.id != False:
                if doc.purchase_id.langsung == True:
                    doc.isDirect = 'Direct to Customer'

    @api.model
    def create(self, vals):
        ww = 4
        return super(StockPickingEnhanced, self).create(vals)

    @api.multi
    def unlink(self):
        ret = True
        for doc in self:
            yy = self.env['em.request.product'].search([('moveopr','=',doc.display_name)])
            for xx in yy:
                xx.moveopr = 'Dihapus'
            zz = self.env['em.return'].search([('kode_move','=',doc.display_name)])
            for uu in zz:
                uu.kode_move = 'Dihapus'
                uu.stat = 'done'
        return super(StockPickingEnhanced, self).unlink()

    @api.multi
    def action_assign(self):
        self.filtered(lambda picking: picking.state == 'draft').action_confirm()
        moves = self.mapped('move_lines').filtered(lambda move: move.state not in ('draft', 'cancel', 'done'))
        if not moves:
            raise UserError(_('Nothing to check the availability for.'))
        moves._action_assign()
        if self.idmr != False:
            idloc = self.location_id.id
            for doc in self.move_lines:
                idres = doc.product_id.id
                reser = doc.reserved_availability
                prodmr = self.env['em.request.product'].search([('mr_id','=',self.idmr.id),('barang_id','=',idres),('gudang_pengambilan','=',idloc)])
                if len(prodmr) > 0:
                    prodmr[0].direserve = reser
                # else:
                #     raise UserError('Data Material Request tidak ditemukan')
        return True

    @api.multi
    def action_done(self):
        if len(self.idmr) > 0:
            idloc = self.location_id.id
            for doc in self.move_lines:
                idres = doc.product_id.id
                reser = doc.quantity_done
                prodmr = self.env['em.request.product'].search([('mr_id','=',self.idmr.id),('barang_id','=',idres),('gudang_pengambilan','=',idloc)])
                if len(prodmr) > 0:
                    atc = prodmr[0].dikirim
                    prodmr[0].dikirim = atc + doc.quantity_done
                    if prodmr[0].dikirim == prodmr[0].permintaan:
                        prodmr[0].statx = 'done'
                        prodmr[0].direserve = 0
                    else:
                        prodmr[0].statx = 'parsial'
                        prodmr[0].direserve = doc.reserved_availability
                    aa = self.env['em.onhand'].search([('barang_id','=',idres),('task_idx','=',self.idtask.id)])
                    if len(aa) > 0:
                        aa[0].quantity = aa[0].quantity + doc.quantity_done
                        aa[0].cost_center_id = doc.cost_center_id.id
                        aa[0].analytic_account_id = doc.analytic_account_id.id
                    else:
                        isix = {'barang_id':idres,
                                'quantity':doc.quantity_done,
                                'cost_center_id':doc.cost_center_id.id,
                                'analytic_account_id':doc.analytic_account_id.id,
                                'task_idx':self.idtask.id}
                        self.env['em.onhand'].create(isix)
        if len(self.idreturn) > 0:
            for doc in self.move_lines:
                # update stock product
                vv = self.env['em.return.products'].search([('ret_id','=',self.idreturn.id),('barang_id','=',doc.product_id.id)])
                if len(vv) > 0:
                    vv[0].ret_done = vv[0].ret_done + doc.quantity_done
                    vv[0].ret_pros = vv[0].ret_pros - doc.quantity_done
                # update stock onhand
                aa = self.env['em.onhand'].search([('barang_id','=',doc.product_id.id),('task_idx','=',self.idreturn.task_idx.id)])
                if len(aa) > 0:
                    aa[0].ret = aa[0].ret + doc.quantity_done
                    aa[0].cost_center_id = doc.cost_center_id.id
                    aa[0].analytic_account_id = doc.analytic_account_id.id
                ww = 4
            # update dokumen return jadi done
            self.idreturn.stat = 'done'
            ww = 4
        return super(StockPickingEnhanced, self).action_done()
