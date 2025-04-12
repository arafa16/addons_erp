from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import float_is_zero


class bill_quantity_line(models.Model):
    _name = 'bill.quantity.line'
    _description = 'Bill Of Quantity Line'
    _inherit = ['mail.thread']
    _rec_name = 'bill_quantity_id'

    def _get_domain_rfq(self):
        group_rfq_id = self.sudo().env.ref('bill_of_quantity_kopkarla.group_rfi_officer').id
        return [('groups_id', 'in', [group_rfq_id])]

    bill_quantity_id = fields.Many2one('bill.quantity', string='BoQ No.', ondelete='cascade', index=True)
    crm_id = fields.Many2one('crm.lead', 'CRM', related='bill_quantity_id.crm_id')
    crm_stage_id = fields.Many2one('crm.stage', related='crm_id.stage_id')
    key = fields.Selection(
        [
            # ('labor', 'Labor'),
            ('material', 'Material'),
            ('operational', 'Operational'),
            ('permit', 'Permit'),
            ('mitra', 'Mitra'),
            ('asset', 'Asset'),
        ], 'Key')
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True)
    # employee_id = fields.Many2one('hr.employee', 'Employee', )
    asset_id = fields.Many2one('maintenance.equipment', string='Assets', ondelete='restrict', index=True)
    # partner_id = fields.Many2one('res.partner', string='Partners', )

    # work_package_id = fields.Many2one('work.package', string='Work Package', ondelete='set null')
    cost_code_id = fields.Many2one('cost.code', string='Cost Code', ondelete='restrict', index=True)

    # type = fields.Char('Type', size=64,)
    product_brand = fields.Char('Brand')
    product_type = fields.Char('Type')
    name = fields.Text('Description')
    lokasi_kirim = fields.Char('Lokasi Kirim')

    expired_date = fields.Date('Expired Date')
    delivery = fields.Char('Delivery Time')
    franco = fields.Char('Franco')
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Term')

    garansi = fields.Char('Garansi')
    cost_center_id = fields.Many2one("cost.center", string="Cost Center", related='crm_id.cost_center_id')
    area_id = fields.Many2one('enhanced.sales.area', string='Sales Area', related='crm_id.area_id')
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account', related='crm_id.analytic_account_id') #, required=True)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure',)
    qty = fields.Float("Qty", default=1)
    price_unit = fields.Float("Cost", default = 0.0,)
    price_service = fields.Float("Cost Service", default = 0.0,)
    price_subtotal = fields.Float("Subtotal", compute='_compute_price', default = 0.0, readonly=True, store=True,)
    service_subtotal = fields.Float("Subtotal Service", compute='_compute_price', default = 0.0, readonly=True, store=True,)
    sale_price = fields.Float("Sales Material", default = 0.0,)
    sale_service = fields.Float("Sales Service", default = 0.0,)
    sale_subtotal = fields.Float("Subtotal Sales Material", compute='_compute_price', default = 0.0, readonly=True, store=True,)
    sale_service_subtotal = fields.Float("Subtotal Sales Service", compute='_compute_price', default = 0.0, readonly=True, store=True,)
    revenue_margin = fields.Float('Margin (%)') #, compute='_compute_price')
    boq_state = fields.Selection([
        ('draft', 'Draft'),
        ('to_rfi', 'To RFI'),
        ('posted', 'Posted'),
        ('cancel', 'Canceled')
    ], string='BoQ State', related='bill_quantity_id.state')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'Process'),
        ('done', 'Done'),
        ('reject', 'Rejected'),
        ('cancel', 'Canceled'),
    ], string='Status', default='draft', track_visibility='onchange')
    rfi_send = fields.Boolean('Send to RFI')
    rfi_id = fields.Many2one('bill.quantity.rfi', string='Selected RFI', ondelete='set null', index=True, track_visibility='onchange')
    rfi_expired_date = fields.Date('Expired Date', related='rfi_id.expired_date', store=True)
    rfi_expired = fields.Boolean('RFI Expired', compute='_get_rfi_expired_date')
    product_rfi_ids = fields.One2many('bill.quantity.rfi', 'bill_quantity_line_id', string='Product Price', track_visibility='onchange')
    user_id = fields.Many2one('res.users', string='Presales Person', related='bill_quantity_id.user_id')
    user_rfq_id = fields.Many2one('res.users', string='RFI Person', index=True, track_visibility='onchange', domain=_get_domain_rfq)
    # penawaran_harga = fields.Selection([('single', '1 Price'), ('double', '2 Price')], 'Penawaran Harga', default='single')
    # boq_date = fields.Datetime('Tanggal Input Sales', related='bill_quantity_id.create_date')
    boq_due_date = fields.Date('BoQ Due Date', related='bill_quantity_id.boq_due_date')
    rfi_due_date = fields.Date('RFI Due Date', related='bill_quantity_id.rfi_due_date', store=True)
    alamat_pengiriman = fields.Char('Alamat Pengiriman', related='crm_id.end_user_address')
    # divisi = fields.Selection([('pusat', 'Pusat'), ('regional', 'Regional')], 'Divisi')
    product_price_count = fields.Integer('Product Price History', compute='_get_product_price_count')
    close_date = fields.Datetime('Closed Date', track_visibility='onchange')
    allow_set_vendor = fields.Boolean(compute='_get_allow_set_vendor')
    allow_set_sales = fields.Boolean(compute='_get_allow_set_sales', default=True)

    count_attachment = fields.Integer(compute='_compute_attachment', string="@")

    notes = fields.Text('Notes')
    boq_line_activity_ids = fields.One2many('bill.quantity.line.activity', 'boq_line_id', string='Activity')

    reject_reason = fields.Char('Rejected Reason')

    def _get_allow_set_vendor(self):
        for line in self:
            line.allow_set_vendor = line.state == 'done' and line.rfi_send

    def _get_allow_set_sales(self):
        for line in self:
            line.allow_set_sales = line.bill_quantity_id.allow_post or not line.bill_quantity_id.total_sale

    @api.multi
    def _compute_attachment(self):
        for rec in self:
            rec.count_attachment = self.env['ir.attachment'].search_count([
                ('res_model', '=', rec._name),
                ('res_id', '=', rec.id),
            ])

    @api.multi
    def action_view_employee_attachment(self):
        return {
            'name': 'Attachment',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            }
        }

    def _get_rfi_expired_date(self):
        for line in self:
            if line.rfi_expired_date:
                line.rfi_expired = line.rfi_expired_date < fields.Datetime.now()
            else:
                line.rfi_expired = False

    @api.multi
    def show_bill_quantity_select_vendor(self):
        self.env['bill.quantity.select.vendor'].sudo().search([]).unlink()
        self.env['bill.quantity.select.vendor.line'].sudo().search([]).unlink()
        action = self.env.ref('bill_of_quantity_kopkarla.action_bill_quantity_select_vendor').read()[0]
        action['context'] = {
            'default_bill_quantity_line_id': self.id,
        }
        return action

    @api.multi
    def show_rfi_product_price(self):
        return {
            'name': _('Product Price History'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'bill.quantity.rfi',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('product_id', '=', self.product_id.id)],
        }

    def _get_product_price_count(self):
        for line in self:
            line.product_price_count = len(self.env['bill.quantity.rfi'].sudo().search([('product_id', '=', line.product_id.id)]))

    @api.onchange('rfi_id')
    def _onchange_rfi(self):
        self.price_unit = 0
        if self.rfi_id:
            self.price_unit = self.rfi_id.price_unit
            self.expired_date = self.rfi_id.expired_date
            self.delivery = self.rfi_id.delivery
            self.franco = self.rfi_id.franco
            self.payment_term_id = self.rfi_id.payment_term_id.id
            self.garansi = self.rfi_id.garansi

    @api.onchange('revenue_margin')
    def _compute_sale_price(self):
        for i in self:
            if i.key == 'material':
                sale_subtotal = i.sale_subtotal + i.sale_service_subtotal
                margin = sale_subtotal * i.revenue_margin / 100
                margin_cost = sale_subtotal - (i.price_subtotal + i.service_subtotal)
                while not float_is_zero(margin - margin_cost, precision_digits=5):
                    sale_subtotal = i.price_subtotal + margin
                    margin_cost = sale_subtotal - i.price_subtotal
                    margin = sale_subtotal * i.revenue_margin / 100
                i.sale_price = sale_subtotal / i.qty
                i._compute_price()

    @api.onchange('price_unit', 'price_service', 'sale_price', 'sale_service', 'qty', 'product_id')
    def _onchange_quantity_price(self):
        for i in self:
            i.price_subtotal = i.qty * i.price_unit
            i.service_subtotal = i.qty * i.price_service
            i.sale_subtotal = i.qty * i.sale_price
            i.sale_service_subtotal = i.qty * i.sale_service
            i.revenue_margin = (((i.sale_subtotal + i.sale_service_subtotal) - (i.price_subtotal + i.service_subtotal)) / (i.sale_subtotal + i.sale_service_subtotal) * 100) if (i.sale_subtotal + i.sale_service_subtotal) != 0 else 0

    @api.depends('price_unit', 'price_service', 'sale_price', 'sale_service', 'qty', 'product_id')
    def _compute_price(self):
        for i in self:
            i.price_subtotal = i.qty * i.price_unit
            i.service_subtotal = i.qty * i.price_service
            i.sale_subtotal = i.qty * i.sale_price
            i.sale_service_subtotal = i.qty * i.sale_service
            # i.revenue_margin = (((i.sale_subtotal + i.sale_service_subtotal) - (i.price_subtotal + i.service_subtotal)) / (i.sale_subtotal + i.sale_service_subtotal) * 100) if (i.sale_subtotal + i.sale_service_subtotal) != 0 else 0

    @api.onchange("product_id")
    def _onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                name = rec.product_id.name
                if rec.product_id.code:
                    name = "[{}] {}".format(name, rec.product_id.code)
                if rec.product_id.description_purchase:
                    name += "\n" + rec.product_id.description_purchase
                rec.description = name
                rec.product_brand = rec.product_id.product_brand
                rec.product_type = rec.product_id.product_type
                rec.uom_id = rec.product_id.uom_id.id
                rec.qty = 1
                # if rec.bill_quantity_id.using_mitra:
                rec.price_unit = 0
                if not rec.rfi_send:
                    rec.price_unit = rec.product_id.standard_price

    @api.onchange("asset_id")
    def _onchange_asset_id(self):
        for rec in self:
            if rec.asset_id:
                name = rec.asset_id.name
                # if rec.product_id.code:
                #     name = "[{}] {}".format(name, rec.product_id.code)
                # if rec.product_id.description_purchase:
                #     name += "\n" + rec.product_id.description_purchase
                rec.name = name
                # rec.uom_id = rec.work_package_id.uom_id.id
                rec.qty = 1
                # rec.price_unit = rec.work_package_id.work_package_cost
                # rec.sale_price = rec.work_package_id.work_package_cost

    @api.onchange("cost_code_id")
    def _onchange_cost_code_id(self):
        for rec in self:
            if rec.cost_code_id:
                name = rec.cost_code_id.name
                # if rec.product_id.code:
                #     name = "[{}] {}".format(name, rec.product_id.code)
                # if rec.product_id.description_purchase:
                #     name += "\n" + rec.product_id.description_purchase
                rec.name = name
                rec.uom_id = rec.cost_code_id.uom_id.id
                rec.qty = 1 #rec.cost_code_id.qty
                rec.price_unit = rec.cost_code_id.price_unit
                rec.price_service = rec.cost_code_id.price_service
                rec.sale_price = rec.cost_code_id.sale_unit
                rec.sale_service = rec.cost_code_id.sale_service

    def action_post(self):
        for boq in self:
            # boq._validate_rfi()
            boq.close_date = datetime.now()
            boq.state = 'done'

    def action_process(self):
        for boq in self:
            boq.state = 'process'

    def action_draft(self):
        for boq in self:
            boq.state = 'draft'

    # def action_reject(self):
    #     for boq in self:
    #         boq.state = 'reject'

    def action_cancel(self):
        for boq in self:
            boq.state = 'cancel'

    @api.multi
    def write(self, vals):
        def get_create_data(data):
            body = ''
            for key, value in data.items():
                if key not in ('product_id', 'partner_id'):
                    if key == 'payment_term_id':
                        value = self.env['account.payment.term'].sudo().browse(value).name if value else False
                    body += "<li style='margin-left: 20px;'>%s: %s</li>" % (key, value)
            return body

        def get_update_data(data, boq_vendor_id):
            body = ''
            for key, value in data.items():
                if key not in ('product_id', 'partner_id'):
                    if key == 'payment_term_id':
                        value = self.env['account.payment.term'].sudo().browse(value).name if value else False
                        value_prev = getattr(boq_vendor_id, key).name
                    else:
                        value_prev = getattr(boq_vendor_id, key)
                    body += "<li style='margin-left: 20px;'>%s: %s -> %s</li>" % (key, value_prev, value)
            return body

        if vals.get('product_rfi_ids'):
            for val in vals.get('product_rfi_ids'):
                subject = False
                if val[0] == 0:
                    partner_id = self.env['res.partner'].sudo().browse(val[2].get('partner_id'))
                    subject = 'BoQ Vendor Price Create %s - %s: %s' % (self.bill_quantity_id.name, self.product_id.name, partner_id.name)
                    body = """
                        <b>Vendor Price Create %s</b>
                        <br/>%s
                    """ % (partner_id.name, get_create_data(val[2]))
                elif val[0] == 1:
                    boq_vendor_id = self.env['bill.quantity.rfi'].sudo().browse(val[1])
                    partner_id = boq_vendor_id.partner_id
                    subject = 'BoQ Vendor Price Update %s - %s: %s' % (self.bill_quantity_id.name, self.product_id.name, partner_id.name)
                    body = """
                        <b>Vendor Price Update %s</b>
                        <br/>%s
                    """ % (partner_id.name, get_update_data(val[2], boq_vendor_id))
                elif val[0] == 2:
                    boq_vendor_id = self.env['bill.quantity.rfi'].sudo().browse(val[1])
                    partner_id = boq_vendor_id.partner_id
                    subject = 'BoQ Vendor Price Delete %s - %s: %s' % (self.bill_quantity_id.name, self.product_id.name, partner_id.name)
                    body = """
                        <b>Vendor Price Delete %s</b>
                        <br/>
                        
                    """ % partner_id.name
                if subject:
                    self.env['mail.message'].create({
                        'subject': subject,
                        'body': body,
                        'model': 'bill.quantity.line',
                        'res_id': self.id,
                        'message_type': 'notification',
                        'subtype_id': 1,
                    })
        return super(bill_quantity_line, self).write(vals)

    @api.multi
    def action_rfi_send(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('bill_of_quantity_kopkarla', 'email_template_rfi')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'bill.quantity.line',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            # 'custom_layout': "purchase.mail_template_data_notification_email_purchase_order",
            # 'purchase_mark_rfq_sent': True,
            'force_email': True
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
