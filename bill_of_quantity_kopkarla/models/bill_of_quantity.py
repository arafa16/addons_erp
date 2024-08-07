from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


class Bill_Quantity(models.Model):
    _name = 'bill.quantity'
    _description = 'Bill Quantity'
    _inherit = ['mail.thread']
    _order = "id desc"

    crm_id = fields.Many2one('crm.lead', 'CRM', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    revision = fields.Integer('Revision', readonly=True)
    name = fields.Char('Bill of Quantity', required=True, copy=False, default='New', readonly=True)
    boq_type = fields.Selection([('sale', 'Sales'), ('internal', 'Internal')], string="BoQ Type", default='sale')
    date = fields.Date('Date', default=datetime.now(), readonly=True, states={'draft': [('readonly', False)]})
    boq_due_date = fields.Date('BoQ Due Date', related='crm_id.boq_due_date')
    rfi_due_date = fields.Date('RFI Due Date', readonly=True, states={'draft': [('readonly', False)]})
    close_date = fields.Datetime('Closed Date')
    partner_id = fields.Many2one('res.partner', string='Customer', related='crm_id.partner_id')
    parent_id = fields.Many2one('bill.quantity')

    material_cost_before_discount = fields.Float('Material Cost Before Discount', compute="_compute_amount")
    material_cost = fields.Float('Material Cost', compute="_compute_amount")
    material_sale_before_discount = fields.Float('Material Sales Before Discount', compute="_compute_amount")
    material_sale = fields.Float('Material Sales', compute="_compute_amount")
    line_material_ids = fields.One2many('bill.quantity.line', 'bill_quantity_id', string='Bill Of Quantity Lines',
                                        # readonly=True, states={'draft': [('readonly', False)]},
                                        readonly=False,
                                        copy=True, domain=[('key', '=', 'material')])
    disc_material_cost_pct = fields.Float('Disc. Cost Material', default=0, readonly=True, states={'draft': [('readonly', False)]})
    disc_material_cost_amt = fields.Float('Disc. Cost Material Amount', default=0, readonly=True, states={'draft': [('readonly', False)]})
    disc_material_sale_pct = fields.Float('Disc. Sales Material', default=0, readonly=True, states={'draft': [('readonly', False)]})
    disc_material_sale_amt = fields.Float('Disc. Sales Material Amount', default=0, readonly=True, states={'draft': [('readonly', False)]})

    operational_cost = fields.Float('Operational Cost', compute="_compute_amount")
    line_operational_ids = fields.One2many('bill.quantity.line', 'bill_quantity_id', string='Operational Lines',
                                           # readonly=True, states={'draft': [('readonly', False)]},
                                           readonly=False,
                                           copy=True, domain=[('key', '=', 'operational')])

    permit_cost = fields.Float('Permit Cost', compute="_compute_amount")
    line_permit_ids = fields.One2many('bill.quantity.line', 'bill_quantity_id', string='Permit Lines',
                                      # readonly=True, states={'draft': [('readonly', False)]},
                                      readonly=False,
                                      copy=True, domain=[('key', '=', 'permit')])

    mitra_cost = fields.Float('Mitra Cost', compute="_compute_amount")
    mitra_sale = fields.Float('Mitra Sales', compute="_compute_amount")
    line_mitra_ids = fields.One2many('bill.quantity.line', 'bill_quantity_id', string='Mitra Lines',
                                     # readonly=True, states={'draft': [('readonly', False)]},
                                     readonly=False,
                                     copy=True, domain=[('key', '=', 'mitra')])
    disc_mitra_cost_pct = fields.Float('Disc. Cost Mitra', default=0, readonly=True, states={'draft': [('readonly', False)]})
    disc_mitra_cost_amt = fields.Float('Disc. Cost Mitra Amount', default=0, readonly=True, states={'draft': [('readonly', False)]})
    disc_mitra_sale_pct = fields.Float('Disc. Sales Mitra', default=0, readonly=True, states={'draft': [('readonly', False)]})
    disc_mitra_sale_amt = fields.Float('Disc. Sales Mitra Amount', default=0, readonly=True, states={'draft': [('readonly', False)]})

    total_cost = fields.Float('Total Cost', compute="_compute_amount", store=True)
    total_sale = fields.Float('Total Sales', compute="_compute_amount", store=True)

    overhead_amount = fields.Float('Biaya Overhead', compute='_compute_amount')
    margin_amount = fields.Float('Margin Amount', compute='_compute_amount', store=True)
    margin_pct = fields.Float('Margin', compute='_compute_amount', store=True)

    asset_cost = fields.Float('Asset Cost', compute="_compute_amount")
    line_asset_ids = fields.One2many('bill.quantity.line', 'bill_quantity_id', string='Asset Lines', readonly=False, copy=True, domain=[('key', '=', 'asset')])

    line_material_count = fields.Integer('Material Count', compute='_get_material_count')
    line_operational_count = fields.Integer('Material Count', compute='_get_operational_count')
    line_permit_count = fields.Integer('Material Count', compute='_get_permit_count')
    line_mitra_count = fields.Integer('Material Count', compute='_get_mitra_count')
    line_asset_count = fields.Integer('Material Count', compute='_get_asset_count')

    user_id = fields.Many2one('res.users', string='Presales Person', index=True, track_visibility='onchange', related='crm_id.presales_user_id')
    order_type_id = fields.Many2one('crm.order.type', 'Order Type', related='crm_id.order_type_id', store=True)
    overhead_pct = fields.Float('Overhead (%)') #, related='order_type_id.overhead_pct', store=True)
    using_mitra = fields.Boolean('BoQ Mitra', related='order_type_id.using_mitra', store=True)
    is_rental = fields.Boolean(related='order_type_id.is_rental')
    rental_type = fields.Selection([('Sewa Beli', 'Sewa Beli'), ('Sewa Pakai', 'Sewa Pakai'), ('Back to Back', 'Back to Back'),], 'Rental Type', track_visibility='onchange')
    rental_period = fields.Integer('Masa Sewa')
    rental_uom_id = fields.Many2one('product.uom', string='UoM', domain=[('category_id', '=', 6)])
    resalas_amount = fields.Float('RV')

    # team_id = fields.Many2one('crm.team', string='Sales Channel', oldname='section_id', default=lambda self: self.env['crm.team'].sudo()._get_default_team_id(user_id=self.env.uid),
    #     index=True, track_visibility='onchange', help='When sending mails, the default email address is taken from the sales channel.')
    cost_center_id = fields.Many2one("cost.center", string="Cost Center", related='crm_id.cost_center_id')
    area_id = fields.Many2one('enhanced.sales.area', string='Sales Area', related='crm_id.area_id')
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account', related='crm_id.analytic_account_id') #, required=True)
    rfi_expired_date = fields.Date('RFI Expired Date', compute='_get_rfi_expired_date', store=True)
    boq_rfi_expired = fields.Boolean('BoQ Expired', compute='_get_rfi_expired_date')
    crm_stage_id = fields.Many2one('crm.stage', related='crm_id.stage_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_rfi', 'To RFI'),
        ('calculation', 'Calculation'),
        ('approval', 'Approval'),
        ('posted', 'Posted'),
        ('cancel', 'Canceled')
    ], string='Status', default='draft', track_visibility='onchange')
    notes = fields.Text('Notes')
    allow_post = fields.Boolean(compute='_get_allow_post')
    allow_cancel = fields.Boolean(compute='_get_allow_cancel')
    allow_to_rfi = fields.Boolean(compute='_get_allow_to_rfi_calculation')
    allow_calculation = fields.Boolean(compute='_get_allow_to_rfi_calculation')

    @api.onchange('order_type_id')
    def _onchange_order_type_id(self):
        if self.order_type_id:
            self.overhead_pct = self.order_type_id.overhead_pct
        else:
            self.overhead_pct = 0

    @api.onchange('crm_id')
    def _onchange_crm_id(self):
        if self.is_rental:
            self.rental_type = self.crm_id.rental_type

    def _get_material_count(self):
        for boq in self:
            boq.line_material_count = len(boq.line_material_ids)

    def _get_operational_count(self):
        for boq in self:
            boq.line_operational_count = len(boq.line_operational_ids)

    def _get_permit_count(self):
        for boq in self:
            boq.line_permit_count = len(boq.line_permit_ids)

    def _get_mitra_count(self):
        for boq in self:
            boq.line_mitra_count = len(boq.line_mitra_ids)

    def _get_asset_count(self):
        for boq in self:
            boq.line_asset_count = len(boq.line_asset_ids)

    @api.multi
    def action_show_boq_material(self):
        self.ensure_one()
        action = self.env.ref('bill_of_quantity_kopkarla.act_open_boq_line').read()[0]
        action['domain'] = [
            ('key', '=', 'material')
        ]
        action['context'] = {
            'search_default_bill_quantity_id': self.id,
            'default_bill_quantity_id': self.id,
            'default_key': 'material',
        }
        return action

    def action_show_boq_operational(self):
        self.ensure_one()
        action = self.env.ref('bill_of_quantity_kopkarla.act_open_boq_line').read()[0]
        action['domain'] = [
            ('key', '=', 'operational')
        ]
        action['context'] = {
            'search_default_bill_quantity_id': self.id,
            'default_bill_quantity_id': self.id,
            'default_key': 'material',
        }
        return action

    def action_show_boq_permit(self):
        self.ensure_one()
        action = self.env.ref('bill_of_quantity_kopkarla.act_open_boq_line').read()[0]
        action['domain'] = [
            ('key', '=', 'permit')
        ]
        action['context'] = {
            'search_default_bill_quantity_id': self.id,
            'default_bill_quantity_id': self.id,
            'default_key': 'material',
        }
        return action

    def action_show_boq_mitra(self):
        self.ensure_one()
        action = self.env.ref('bill_of_quantity_kopkarla.act_open_boq_line').read()[0]
        action['domain'] = [
            ('key', '=', 'mitra')
        ]
        action['context'] = {
            'search_default_bill_quantity_id': self.id,
            'default_bill_quantity_id': self.id,
            'default_key': 'material',
        }
        return action

    def action_show_boq_asset(self):
        self.ensure_one()
        action = self.env.ref('bill_of_quantity_kopkarla.act_open_boq_line').read()[0]
        action['domain'] = [
            ('key', '=', 'asset')
        ]
        action['context'] = {
            'search_default_bill_quantity_id': self.id,
            'default_bill_quantity_id': self.id,
            'default_key': 'material',
        }
        return action

    def _get_allow_post(self):
        for boq in self:
            boq.allow_post = ((boq.state == 'draft' and boq.using_mitra) or (boq.state == 'to_rfi' and not boq.using_mitra)) and boq.total_sale

    def _get_allow_to_rfi_calculation(self):
        for boq in self:
            boq.allow_to_rfi = boq.state == 'draft' and True in boq.line_material_ids.mapped('rfi_send')
            boq.allow_calculation = (boq.state == 'draft' and boq.allow_to_rfi == False) or boq.state == 'to_rfi'

    def _get_allow_cancel(self):
        for boq in self:
            boq.allow_cancel = boq.state != 'cancel'

    @api.onchange('line_material_ids', 'line_material_ids.rfi_id', 'line_material_ids.rfi_due_date')
    def _get_rfi_expired_date(self):
        for boq in self:
            if False in boq.line_material_ids.mapped('rfi_expired_date') or not len(boq.line_material_ids):
                boq.rfi_expired_date = False
                boq.boq_rfi_expired = False
            else:
                boq.rfi_expired_date = min(boq.line_material_ids.mapped('rfi_expired_date'))
                boq.boq_rfi_expired = boq.rfi_expired_date < fields.Datetime.now()

    @api.depends('line_material_ids.qty', 'line_material_ids.price_unit',
                 'disc_material_cost_pct', 'disc_material_cost_amt',
                 'disc_material_sale_pct', 'disc_material_sale_amt',
                 'line_operational_ids.qty', 'line_operational_ids.price_unit',
                 'line_permit_ids.qty', 'line_permit_ids.price_unit',
                 'line_mitra_ids.qty', 'line_mitra_ids.price_unit',
                 'disc_mitra_cost_pct', 'disc_mitra_cost_amt',
                 'disc_mitra_sale_pct', 'disc_mitra_sale_amt', 'resalas_amount',
                 'overhead_pct')
    def _compute_amount(self):
        for i in self:
            material_price_subtotal_before_discount = 0.0
            material_price_subtotal = 0.0
            material_sale_subtotal_before_discount = 0.0
            material_sale_subtotal = 0.0
            operational_price_subtotal = 0.0
            permit_price_subtotal = 0.0
            mitra_price_subtotal = 0.0
            mitra_sale_subtotal = 0.0

            if i.line_material_ids:
                for record in i.line_material_ids:
                    if record.key == 'material':
                        material_price_subtotal_before_discount += record.price_subtotal
                        material_price_subtotal += record.price_subtotal
                        material_sale_subtotal_before_discount += record.sale_subtotal
                        material_sale_subtotal += record.sale_subtotal
            disc_material_cost = -material_price_subtotal * i.disc_material_cost_pct / 100
            disc_material_sale = -material_sale_subtotal * i.disc_material_sale_pct / 100
            material_price_subtotal += disc_material_cost
            material_sale_subtotal += disc_material_sale

            if i.line_operational_ids:
                for record in i.line_operational_ids:
                    if record.key == 'operational':
                        operational_price_subtotal += record.price_subtotal

            if i.line_permit_ids:
                for record in i.line_permit_ids:
                    if record.key == 'permit':
                        permit_price_subtotal += record.price_subtotal

            if i.line_mitra_ids:
                for record in i.line_mitra_ids:
                    if record.key == 'mitra':
                        mitra_price_subtotal += record.price_subtotal + record.service_subtotal
                        mitra_sale_subtotal += record.sale_subtotal + record.sale_service_subtotal
            disc_mitra_cost = -mitra_price_subtotal * i.disc_mitra_cost_pct / 100
            disc_mitra_sale = -mitra_sale_subtotal * i.disc_mitra_sale_pct / 100

            # total_sale = material_sale_subtotal + operational_price_subtotal + permit_price_subtotal + mitra_sale_subtotal + disc_mitra_sale
            total_sale = material_sale_subtotal + mitra_sale_subtotal + disc_mitra_sale + i.resalas_amount
            # overhead_amount = total_sale * i.order_type_id.overhead_pct / 100
            overhead_amount = total_sale * i.overhead_pct / 100
            total_cost = material_price_subtotal + operational_price_subtotal + permit_price_subtotal + mitra_price_subtotal + disc_mitra_cost + overhead_amount
            margin_amount = total_sale - total_cost
            margin_pct = (margin_amount / total_sale * 100) if total_sale != 0 else 0
            i.update({'material_cost_before_discount': material_price_subtotal_before_discount,
                      'disc_material_cost_amt': disc_material_cost,
                      'material_cost': material_price_subtotal,
                      'material_sale_before_discount': material_sale_subtotal_before_discount,
                      'disc_material_sale_amt': disc_material_sale,
                      'material_sale': material_sale_subtotal,
                      'operational_cost': operational_price_subtotal,
                      'permit_cost': permit_price_subtotal,
                      'mitra_cost': mitra_price_subtotal,
                      'disc_mitra_cost_amt': disc_mitra_cost,
                      'mitra_sale': mitra_sale_subtotal,
                      'disc_mitra_sale_amt': disc_mitra_sale,
                      'total_cost': total_cost,
                      'total_sale': total_sale,
                      'overhead_amount': overhead_amount,
                      'margin_amount': margin_amount,
                      'margin_pct': margin_pct
                      })

    @api.model
    def create(self, vals):
        # if vals.get('name') == 'New':
        vals['name'] = self.env['ir.sequence'].next_by_code('boq.number.sequence') or 'New'
        return super(Bill_Quantity, self).create(vals)

    def validate_boq(self):
        if self.total_cost <= 0:
            raise UserError(_("Total cost 0."))

    def _update_project_boq(self, _set_status, boq):
        if _set_status:
            boq.crm_id.planned_revenue = boq.total_sale
        # else:
        #     boq.crm_id.planned_revenue = 0

    def action_to_rfi(self):
        for boq in self:
            boq.state = 'to_rfi'

    def action_calculation(self):
        for boq in self:
            boq.state = 'calculation'

    def action_approval(self):
        for boq in self:
            boq.state = 'approval'

    def action_post(self):
        for boq in self:
            boq.validate_boq()
            if boq.crm_id:
                boq._update_project_boq(True, boq)
            boq.write({'close_date': datetime.now(), 'state': 'posted'})

    def action_draft(self):
        for boq in self:
            boq.state = 'draft'

    def action_cancel(self):
        for boq in self:
            # boq._update_project_boq(False, boq)
            boq.state = 'cancel'

    def unlink(self):
        for request in self:
            if not request.state in ('draft', 'cancel'):
                raise UserError(
                    _("You cannot delete a document which is not draft or canceled.")
                )
        return super(Bill_Quantity, self).unlink()

    def get_approver_status(self, approver=False):
        pass