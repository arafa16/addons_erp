from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'    

    ratingx = fields.Selection([ (0, '0'),(1, '1'),(2, '2'),(3, '3'),(4, '4'),(5, '5')], string='Vendor Rating') 
    # rfq = fields.Many2many(comodel_name='sprogroup.purchase.request', string='Purchase Request',domain=[('state', '=', 'done'),('idpo','=',False)])
    nomor_coa = fields.Many2one('account.account', string='Chart Of Account')
    to_rent = fields.Boolean(string='Purchase for Rental')
    rent_date_start = fields.Date(string='Start Date')
    rent_date_end = fields.Date(string='End Date')
    # @api.model
    # def create(self, vals):
    #     aa = vals['rfq']
    #     bb = aa[0][2]
    #     request = super(PurchaseOrder, self).create(vals)
    #     if len(bb) > 0:
    #         for ff in bb:
    #             xx = self.env['sprogroup.purchase.request'].browse(ff)
    #             xx.idpo = request
    #     return request

    @api.multi
    def write(self, vals):
        ww = 4
        res = super(PurchaseOrder, self).write(vals)
        return res