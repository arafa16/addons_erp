from odoo import models, fields, api, _


class bill_quantity_line_rfi(models.Model):
    _name = 'bill.quantity.rfi'
    _description = 'Product RFI'
    _inherit = ['mail.thread']
    _rec_name = 'partner_id'

    bill_quantity_line_id = fields.Many2one('bill.quantity.line', string='BoQ Line', ondelete='set null', index=True)
    bill_quantity_id = fields.Many2one('bill.quantity', string='BoQ No.', related='bill_quantity_line_id.bill_quantity_id')
    crm_id = fields.Many2one('crm.lead', 'CRM', related='bill_quantity_id.crm_id')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', related='bill_quantity_line_id.product_id', index=True, store=True)
    name = fields.Char('Name')
    description = fields.Char('Description')
    # uom_id = fields.Many2one('product.uom', 'Unit of Measure',)
    # qty = fields.Float("Qty", default=1)
    partner_id = fields.Many2one('res.partner', string='Partners', track_visibility='onchange')
    price_unit = fields.Float("Unit Price", default = 0.0, track_visibility='onchange')
    expired_date = fields.Date('Expired Date', track_visibility='onchange')
    delivery = fields.Char('Delivery Time', track_visibility='onchange')
    franco = fields.Char('Franco', track_visibility='onchange')
    garansi = fields.Char('Garansi', track_visibility='onchange')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term', track_visibility='onchange')
    selected = fields.Boolean(compute='_get_selected_status')
    user_rfq_id = fields.Many2one('res.users', string='RFI Person', related='bill_quantity_line_id.user_rfq_id')

    @api.multi
    def action_select_vendor(self):
        self.ensure_one()
        self.bill_quantity_line_id.update({'rfi_id': self.id})
        self.bill_quantity_line_id._onchange_rfi()
        view = self.env.ref('bill_of_quantity_kopkarla.view_bill_quantity_form')
        return {
            'name': 'Bill of Quantity',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'bill.quantity',
            'views': [(view.id, 'form')],
            'target': 'self',
            'res_id': self.bill_quantity_id.id,
        }
        # return {'type': 'ir.actions.act_window_close'}

    def _get_selected_status(self):
        for rfi in self:
            rfi.selected = rfi.bill_quantity_line_id.rfi_id == rfi

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('rfi.number.sequence') or 'New'
        return super(bill_quantity_line_rfi, self).create(vals)

    @api.multi
    def goto_rfi(self):
        view_id = self.env.ref('bill_of_quantity_kopkarla.view_rfi_drill_tree')
        return {
            'name': _('RFI'),
            'type': 'ir.actions.act_window',
            'res_model': 'bill.quantity.rfi',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current', # 'new',  #
            'view_id': view_id.id,
            'views': [(view_id.id, 'form')],
            'res_id': self.id,
        }
