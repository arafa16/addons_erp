# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError


class RFISelectVendor(models.TransientModel):
    _name = 'bill.quantity.select.vendor'
    _description = 'RFI Select Vendor'

    bill_quantity_line_id = fields.Many2one('bill.quantity.line', string='BoQ Line', ondelete='set null', index=True)
    product_rfi_ids = fields.One2many('bill.quantity.select.vendor.line', 'bill_quantity_line_id', string='RFI Product')
    partner_id = fields.Many2one('res.partner', string='Selected Vendor', required=1)

    @api.onchange('bill_quantity_line_id')
    def onchange_bill_quantity_line_id(self):
        rfi_ids = []
        partner_ids = []
        for rfi_id in self.bill_quantity_line_id.product_rfi_ids:
            rfi_data = (0, 0, {
                'bill_quantity_rfi_id': rfi_id.id,
                'crm_id': rfi_id.crm_id.id,
                'product_id': rfi_id.product_id.id,
                'name': rfi_id.name,
                'description': rfi_id.description,
                'partner_id': rfi_id.partner_id.id,
                'price_unit': rfi_id.price_unit,
                'expired_date': rfi_id.expired_date,
                'delivery': rfi_id.delivery,
                'franco': rfi_id.franco,
                'garansi': rfi_id.garansi,
                'payment_term_id': rfi_id.payment_term_id.id,
                # 'selected': rfi_id.selected,
            })
            rfi_ids.append(rfi_data)
            partner_ids.append(rfi_id.partner_id.id)
        self.product_rfi_ids = rfi_ids
        return {
            'domain': {'partner_id': [('id', 'in', partner_ids)]},
        }

    @api.multi
    def execute(self):
        if self.bill_quantity_line_id.allow_set_vendor:
            rfi_id = self.bill_quantity_line_id.product_rfi_ids.filtered(lambda r: r.partner_id.id == self.partner_id.id)
            self.bill_quantity_line_id.rfi_id = rfi_id.id
            self.bill_quantity_line_id._onchange_rfi()
        else:
            raise UserError(_("BoQ sudah / sedang diproses approval!"))


class RFISelectVendor(models.TransientModel):
    _name = 'bill.quantity.select.vendor.line'
    _description = 'RFI Select Vendor Line'
    _rec_name = 'partner_id'

    bill_quantity_line_id = fields.Many2one('bill.quantity.select.vendor', string='BoQ Line', ondelete='cascade', readonly=True)
    bill_quantity_id = fields.Many2one('bill.quantity', string='BoQ No.', related='bill_quantity_line_id.bill_quantity_line_id.bill_quantity_id', readonly=True)
    crm_id = fields.Many2one('crm.lead', 'CRM', related='bill_quantity_id.crm_id')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', related='bill_quantity_line_id.bill_quantity_line_id.product_id', index=True, store=True)
    name = fields.Char('Name', readonly=True)
    description = fields.Char('Description', readonly=False)
    # uom_id = fields.Many2one('product.uom', 'Unit of Measure',)
    # qty = fields.Float("Qty", default=1)
    partner_id = fields.Many2one('res.partner', string='Partners', readonly=True)
    price_unit = fields.Float("Unit Price", default = 0.0, readonly=True)
    expired_date = fields.Date('Expired Date', readonly=True)
    delivery = fields.Char('Delivery Time', readonly=True)
    franco = fields.Char('Franco', readonly=True)
    garansi = fields.Char('Garansi', readonly=True)
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term', readonly=True)
    # selected = fields.Boolean()
