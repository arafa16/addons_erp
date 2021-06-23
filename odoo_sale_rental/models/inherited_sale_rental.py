# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, RedirectWarning

from odoo.tools.translate import _
from odoo.addons import decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

RentalDurationUnits = [
    ('minutes', 'Minute(s)'),
    ('hours', 'Hour(s)'),
    ('days', 'Day(s)'),
    ('weeks', 'Week(s)'),
    ('months', 'Month(s)'),
    ('years', 'Year(s)')
]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # Fields declaration

    is_rental_so = fields.Boolean(
        "Rental Order",
        compute="_compute_rental_so",
        store=True,
    )
    total_deposit_security_amount = fields.Float(
        compute='_calculate_total_security_amount',
        string='Security Deposit',
        required=True,
        digits=dp.get_precision('Product Price'),
        default=0.0,
        store=True,
    )

    sale_contract_count = fields.Integer(
        string='Sale Contracts',
        compute='_compute_contract_count',
    )

    def _compute_contract_count(self):
        contract_model = self.env['account.analytic.account']
        today = fields.Date.today()
        fetch_data = contract_model.read_group([
            ('recurring_invoices', '=', True),
            ('partner_id', '=', self.partner_id.id),
            ('code', '=', self.name)],
            ['partner_id', 'code', 'contract_type'],
            ['partner_id', 'code', 'contract_type'],
            lazy=False)
        result = [[data['partner_id'][0], data['contract_type'],
                   data['__count']] for data in fetch_data]
        for partner in self.partner_id:
            partner_child_ids = partner.child_ids.ids + partner.ids
            self.sale_contract_count = sum([
                r[2] for r in result
                if r[0] in partner_child_ids and r[1] == 'sale'])

    def act_show_contract(self):
        self.ensure_one()

        res = self._get_act_window_contract_xml()
        res.update(
            context=dict(
                self.env.context,
                search_default_recurring_invoices=True,
                search_default_partner_id=self.partner_id.id,
                search_default_code=self.name,
            ),
        )
        return res

    def _get_act_window_contract_xml(self):
        return self.env['ir.actions.act_window'].for_xml_id(
            'contract', 'action_account_analytic_sale_overdue_all')

    # compute and search fields, in the same order of fields declaration

    @api.multi
    @api.depends('order_line.product_id')
    def _compute_rental_so(self):
        for so in self:
            if so.order_line and so.order_line.filtered("is_rental_order"):
                so.is_rental_so = True

    @api.depends('order_line.price_total')
    def _calculate_total_security_amount(self):
        """
        Compute the total security_amount of the Rental SO.
        """
        for order in self:
            if order.is_rental_so:
                deposit_security_amount = 0.0
                for line in order.order_line:
                    deposit_security_amount += line.total_deposit_security_amount
                order.update({
                    'total_deposit_security_amount': deposit_security_amount
                })

    # Constraints and onchanges

    # CRUD methods (and name_get, name_search, pass) overrides

    # Action methods
    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for sol in order.order_line:
                if sol.is_rental_order:
                    sol.next_rental_sol_sequence()
                    sol.rental_contract_ids.action_confirm()
        return res

    # Business methods

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        res = super(SaleOrder, self).action_invoice_create(
            grouped=grouped, final=final)
        for so_obj in self:
            if so_obj.total_deposit_security_amount:
                so_obj.create_deposit_amt_invoice()
        return res

    #Code to create separate invoice for security deposite amount

    @api.multi
    def create_deposit_amt_invoice(self):
        self.ensure_one()
        journal_id = self.env['account.invoice'].default_get(['journal_id'])[
            'journal_id']
        if not journal_id:
            raise UserError(
                _('Please define an accounting sale journal for this company.'))
        invoice_vals = {
            'name': self.client_order_ref or '',
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': self.partner_invoice_id.property_account_payable_id.id,
            'partner_id': self.partner_invoice_id.id,
            'partner_shipping_id': self.partner_shipping_id.id,
            'journal_id': journal_id,
            'currency_id': self.pricelist_id.currency_id.id,
            'comment': self.note,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.user_id and self.user_id.id,
            'team_id': self.team_id.id,
            "invoice_line_ids": [(0, 0, {
                'name': "Deposit security amount for the rental order '%s'" % self.name,
                'quantity': 1,
                "price_unit": self.total_deposit_security_amount,
                'origin': self.name,
                'account_id': self.partner_invoice_id.property_account_payable_id.id,
            })],
        }
        self.env['account.invoice'].create(invoice_vals)


class SaleOrderLine(models.Model):
    """ Inherit sale.order modal to adding addition requirement for rental order"""

    # Private attributes
    _inherit = 'sale.order.line'

    # Default methods

    # Fields declaration
    is_rental_order = fields.Boolean(
        "Rental Order",
        # related="product_id.rental_ok",
        # store=True,
    )
    rental_sequence = fields.Char(
        "Rental Order",
        default=lambda self: _('New'),
    )
    price_subtotal = fields.Monetary(
        compute='_compute_amount',
        string='Subtotal',
        readonly=True,
        store=True,
    )
    price_tax = fields.Float(
        compute='_compute_amount',
        string='Taxes',
        readonly=True,
        store=True,
    )
    price_total = fields.Monetary(
        compute='_compute_amount',
        string='Total',
        readonly=True,
        store=True,
    )
    price_subtotal_with_tax = fields.Monetary(
        compute='_compute_amount',
        string="Final Amount",
        readonly=True,
        store=True,
    )
    price_total_without_tax_security = fields.Monetary(
        compute='_compute_amount',
        string="Total",
        readonly=True,
        store=True,
    )
    price_reduce = fields.Float(
        compute='_get_price_reduce',
        string='Price Reduce',
        digits=dp.get_precision('Product Price'),
        readonly=True,
        store=True,
    )
    price_reduce_taxinc = fields.Monetary(
        compute='_get_price_reduce_tax',
        string='Price Reduce Tax inc',
        readonly=True,
        store=True,
    )
    price_reduce_taxexcl = fields.Monetary(
        compute='_get_price_reduce_notax',
        string='Price Reduce Tax excl',
        readonly=True,
        store=True,
    )
    unit_security_amount = fields.Float(
        'Unit Security Amount',
        required=True,
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    total_deposit_security_amount = fields.Float(
        compute='_compute_amount',
        string='Security Deposit',
        required=True,
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    refunded_security_amount = fields.Float(
        string='Refunded Security Amount',
        required=True,
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    pending_security_amount = fields.Float(
        # compute='_compute_pending_security_amount',
        string='Pending Security Amount',
        required=True,
        digits=dp.get_precision('Product Price'),
        default=0.0,
    )
    rental_uom_id = fields.Many2one(
        "product.uom",
        "Tenure UOM",
        domain=lambda self: [('is_rental_uom', '=', True)],
        readonly=True,
    )
    rental_tenure = fields.Float(
        "Tenure",
        readonly=True,
    )
    rental_start_time = fields.Datetime(
        "Start Time",
        readonly=True,
    )
    rental_end_time = fields.Datetime(
        string='End Time',
        readonly=True,
    )
    security_amount = fields.Float(
        "Security Amount",
        compute='_get_security_amount',
    )

    #Initial renatl contract details
    initial_start_time = fields.Datetime(
        string='Start Time',
        related="inital_rental_contract_id.start_time",
        readonly=True,
        store=True,
    )
    initial_end_time = fields.Datetime(
        string='End Time',
        related="inital_rental_contract_id.end_time",
        readonly=True,
        store=True,
    )
    inital_rental_contract_id = fields.Many2one(
        "rental.order.contract",
        "Initial Contract",
        readonly=True
    )
    last_renewal_time = fields.Datetime(
        "Last Renewal Time",
        readonly=True,
    )

    #Current renatl contract details
    current_start_time = fields.Datetime(
        "Start Time",
        related="current_rental_contract_id.start_time",
        readonly=True,
        store=True,
    )
    current_end_time = fields.Datetime(
        string='End Time',
        related="current_rental_contract_id.end_time",
        readonly=True,
        store=True,
    )
    current_rental_qty = fields.Float(
        "Quantity",
        related="current_rental_contract_id.rental_qty",
        readonly=True,
        store=True,
    )
    current_rental_uom_id = fields.Many2one(
        "product.uom",
        "Tenure UOM",
        domain=lambda self: [('is_rental_uom', '=', True)],
    )
    current_rental_tenure = fields.Float(
        "Tenure",
        readonly=True,
    )
    current_rental_contract_id = fields.Many2one(
        "rental.order.contract",
        "Current Contract",
        readonly=True
    )
    rental_contract_ids = fields.One2many(
        "rental.order.contract",
        "sale_order_line_id",
        "Contracts",
        readonly=True,
        copy=False,
        ondelete='restrict',
    )
    rental_state = fields.Selection([
            ('ordered', 'New'),
            ('confirm', 'Confirm'),
            ('in_progress', 'In progress'),
            ('expired', 'Expired'),
            ('closed', 'Closed'),
            ('cancel', 'Cancelled'),
        ],
        string='Rental Status',
        readonly=True,
        default="ordered",
        help=" * The 'New' status means new Rental order has been generated.\n"
        "* The 'Confirm' status means new Rental order has been confirmed.\n"
        " * The 'In progress' status means product has been delivered customer & rental order is active now.\n"
        " * The 'Expired' status means rental order has been expired now.\n"
        " * The 'Closed' status means rental product has been rececived from customer.\n"
        " * The 'Cancelled' status means rental order has been cancelled now.\n"
    )
    rental_delivery_status = fields.Selection([
            ('delivery_waiting', 'Not Delivered'),
            ('partial_deliver', 'Partial Delivered'),
            ('all_delivered', 'Delivered'),
            ('receiving_waiting', 'Not Received'),
            ('partial_receive', 'Partial Received'),
            ('all_received', 'Received'),
        ],
        string="Delivery Status",
        compute="_compute_rental_delivery_status",
        help="* The 'Not Delivered' status means product(s) not delivered yet.\n"
        " * The 'Partial Delivered' status means some product(s) delivered but some product(s) not.\n"
        " * The 'Delivered' status means all product has been delivered.\n"
        " * The 'Not Received' status means product has been not received from customer.\n"
        " * The 'Partial Received'  status means product has been partially received from customer.\n"
        " * The 'Received'status means product has been received from customer.\n"
    )
    out_picking_count = fields.Integer(
        string='# of Outgoing Delivery',
        compute='_compute_rental_sol_picking_and_counts',
        readonly=True
    )
    in_picking_count = fields.Integer(
        string='# of Incoming Delivery',
        compute='_compute_rental_sol_picking_and_counts',
        readonly=True
    )
    rental_out_picking_ids = fields.Many2many(
        "stock.picking",
        "Delivery Pickings",
        compute='_compute_rental_sol_picking_and_counts'
    )
    rental_in_picking_ids = fields.Many2many(
        "stock.picking",
        "Return Pickings",
        compute='_compute_rental_sol_picking_and_counts'
    )
    rental_invoice_count = fields.Integer(
        string='# of Rental Invoice',
        compute='_compute_rental_invoice',
        readonly=True
    )
    security_refund_invoice_id = fields.Many2one(
        "account.invoice",
        "Security Refund Invoice",
    )

    # compute and search fields, in the same order of fields declaration

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the Rental SO line.
        """
        for line in self:
            if line.is_rental_order:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                product=line.product_id, partner=line.order_id.partner_shipping_id)
                price_tax = sum(t.get('amount', 0.0)
                                for t in taxes.get('taxes', []))
                line.update({
                    'price_tax': price_tax,
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'] + (line.unit_security_amount * line.product_uom_qty),
                    'total_deposit_security_amount': line.unit_security_amount * line.product_uom_qty,
                    'price_subtotal_with_tax': price_tax + taxes['total_excluded'] + (line.unit_security_amount * line.product_uom_qty),
                    'price_total_without_tax_security':  taxes['total_included'] - price_tax,
                })
            else:
                super(SaleOrderLine, line)._compute_amount()

    @api.depends('price_unit', 'discount')
    def _get_price_reduce(self):
        for line in self:
            line.price_reduce = line.price_unit * (1.0 - line.discount / 100.0)

    @api.depends('price_total', 'product_uom_qty')
    def _get_price_reduce_tax(self):
        for line in self:
            line.price_reduce_taxinc = line.price_total / \
                line.product_uom_qty if line.product_uom_qty else 0.0

    @api.depends('price_subtotal', 'product_uom_qty')
    def _get_price_reduce_notax(self):
        for line in self:
            line.price_reduce_taxexcl = line.price_subtotal / \
                line.product_uom_qty if line.product_uom_qty else 0.0

    @api.depends('product_uom_qty', "product_id")
    def _get_security_amount(self):
        for line in self:
            if line.is_rental_order:
                line.security_amount = line.product_uom_qty * line.product_id.security_amount

    @api.multi
    @api.depends("current_rental_contract_id.rental_delivery_status", "inital_rental_contract_id.rental_delivery_status")
    def _compute_rental_delivery_status(self):
        for rental_sol_obj in self:
            if rental_sol_obj.current_rental_contract_id:
                rental_sol_obj.rental_delivery_status = rental_sol_obj.current_rental_contract_id.rental_delivery_status
            elif rental_sol_obj.inital_rental_contract_id:
                rental_sol_obj.rental_delivery_status = rental_sol_obj.inital_rental_contract_id.rental_delivery_status

    @api.multi
    @api.depends(
        'move_ids',
        'move_ids.state',
        'order_id.picking_ids',
        'order_id.picking_ids.state'
    )
    def _compute_rental_sol_picking_and_counts(self):
        for rental_sol_obj in self:
            if rental_sol_obj.order_id.picking_ids:
                rental_out_picking_ids = rental_sol_obj.move_ids.filtered(
                    lambda r: r.picking_type_id.code == "outgoing" and r.product_id == rental_sol_obj.product_id and r.picking_id.id in rental_sol_obj.order_id.picking_ids.ids)
                rental_in_picking_ids = rental_sol_obj.move_ids.filtered(
                    lambda r: r.picking_type_id.code == "incoming" and r.product_id == rental_sol_obj.product_id and r.picking_id.id in rental_sol_obj.order_id.picking_ids.ids)
                rental_sol_obj.out_picking_count = len(
                    rental_out_picking_ids) if rental_out_picking_ids else False
                rental_sol_obj.in_picking_count = len(
                    rental_in_picking_ids) if rental_in_picking_ids else False

    @api.multi
    @api.depends('invoice_lines')
    def _compute_rental_invoice(self):
        for line in self:
            if line.invoice_lines:
                invoice_lines = line.invoice_lines.filtered(
                    lambda r: r.product_id == line.product_id)
                invoice_ids = invoice_lines.filtered(
                    lambda r: r.invoice_id == line.order_id.invoice_ids)
                # invoice_ids = line.order_id.invoice_ids.filtered(
                #     lambda r: r.invoice_line_ids.product_id == line.product_id)
                line.rental_invoice_count = len(
                    invoice_ids) if invoice_ids else False

    # Constraints and onchanges

    # CRUD methods (and name_get, name_search, pass) overrides

    @api.model
    def create(self, values):
        res = super(SaleOrderLine, self).create(values)
        if res and res.is_rental_order:
            res._create_rental_order_contract()
        return res

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.order_id.name))
        return result


    # Action methods
    @api.multi
    def view_outgoing_delivery_order(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        rental_out_picking_ids = self.order_id.picking_ids.filtered(
            lambda r: r.picking_type_id.code == "outgoing" and r.move_lines.filtered(
                lambda sm: sm.product_id == self.product_id))
        if len(rental_out_picking_ids) > 1:
            action['domain'] = [('id', 'in', rental_out_picking_ids.ids)]
        elif rental_out_picking_ids:
            action['views'] = [
                (self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = rental_out_picking_ids.id
        else:
            action['domain'] = [('id', 'in', [])]
        return action

    @api.multi
    def view_return_delivery_order(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        rental_in_picking_ids = self.order_id.picking_ids.filtered(
            lambda r: r.picking_type_id.code == "incoming" and r.move_lines.product_id == self.product_id)
        if len(rental_in_picking_ids) > 1:
            action['domain'] = [('id', 'in', rental_in_picking_ids.ids)]
        elif rental_in_picking_ids:
            action['views'] = [
                (self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = rental_in_picking_ids.id
        else:
            action['domain'] = [('id', 'in', [])]
        return action

    @api.multi
    def action_view_invoice(self):
        self.ensure_one()
        # invoices = self.order_id.invoice_ids.filtered(lambda r: r.invoice_line_ids.product_id == self.product_id)
        invoices = self.env['account.invoice'].sudo().search([('origin', '=', self.order_id.name)])
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [
                (self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def action_renew_rental_order(self):
        self.ensure_one()
        # if slef.security_refund_invoice_id:
        #     raise UserError(_(""))
        in_progress_contract = self.rental_contract_ids.filtered(
            lambda c: c.state in ["new", "in_progress"])
        if in_progress_contract:
            raise UserError(
                _('Rental contract "%r" is already in %r state. You will be able to renew once contract "%r" will get expired.') % (in_progress_contract.name, in_progress_contract.state, in_progress_contract.name))
        action = self.env.ref(
            'odoo_sale_rental.renew_rental_order_wizard_action')
        form_view_id = self.env['ir.model.data'].xmlid_to_res_id(
            'odoo_sale_rental.renew_rental_order_wizard_view_form')
        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'res_model': action.res_model,
        }

    # Business methods.

    @api.multi
    def next_rental_sol_sequence(self):
        """ Create contract sequence """
        for sol in self:
            if sol.is_rental_order:
                sol.rental_sequence = self.env['ir.sequence'].with_context(
                    force_company=sol.company_id.id).next_by_code('rental.sale.order.line') or _('New')

    @api.multi
    def _create_rental_order_contract(self):
        for obj in self:
            inital_rental_contract_id = self.env["rental.order.contract"].create(
                obj._prepare_rental_order_contract())
            if inital_rental_contract_id and len(obj.rental_contract_ids) == 1:
                obj.inital_rental_contract_id = inital_rental_contract_id.id
            else:
                obj.current_rental_contract_id = inital_rental_contract_id.id
                obj.last_renewal_time = fields.Datetime.now

    @api.model
    def _prepare_rental_order_contract(self):
        return {
            "sale_order_line_id": self.id,
            "product_rental_agreement_id": self.product_id.rental_agreement_id.id,
            "rental_qty": self._context.get("rental_qty", False) or self.product_uom_qty,
            "rental_uom_id": self._context.get("rental_uom_id", False) or self.rental_uom_id.id,
            "rental_tenure": self._context.get("rental_tenure", False) or self.rental_tenure,
            "price_unit": self.price_unit,
            "tax_ids": [(6, 0, self.tax_id.ids)],
        }

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.product_id.rental_ok and len(self.rental_contract_ids) == 1:
            res.update({
                "rental_contract_id": self.rental_contract_ids[0].id
            })
        return res

    @api.multi
    def create_security_refund_invoice(self):
        self.ensure_one()
        # if not self.total_deposit_security_amount:
        #     raise UserError(_("There is no security amount to refund."))
        company_id = self.order_id.partner_id.company_id.id
        partner_id = self.order_id.partner_id if not company_id else self.order_id.partner_id.with_context(
            force_company=company_id)
        if partner_id:
            rec_account = partner_id.property_account_receivable_id
            if not rec_account:
                action = self.env.ref('account.action_account_config')
                msg = _(
                    'Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise RedirectWarning(msg, action.id, _(
                    'Go to the configuration panel'))

            account_id = rec_account.id
            payment_term_id = partner_id.property_payment_term_id.id
        for rec in self:
            security_refund_product_id = self.env['ir.default'].sudo().get(
                'res.config.settings', 'security_refund_product_id')
            if security_refund_product_id:
                security_refund_product_obj = self.env["product.product"].browse(
                security_refund_product_id)
                account = security_refund_product_obj.property_account_income_id or security_refund_product_obj.categ_id.property_account_income_categ_id
                if not account:
                    raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                                    (security_refund_product_obj.name, security_refund_product_obj.id, security_refund_product_obj.categ_id.name))

                invoice_vals = {
                    'origin': rec.order_id.name,
                    'type': 'out_refund',
                    'account_id': account_id,
                    'partner_id': rec.order_id.partner_id.id,
                    'partner_shipping_id': rec.order_id.partner_shipping_id.id,
                    'currency_id': rec.order_id.pricelist_id.currency_id.id,
                    'payment_term_id': payment_term_id,
                    'fiscal_position_id': rec.order_id.partner_id.property_account_position_id.id,
                    'company_id': rec.order_id.partner_id.company_id.id,
                }
                invoice_obj = self.env['account.invoice'].create(invoice_vals)
                if invoice_obj:
                    rec.security_refund_invoice_id = invoice_obj.id
                    #create invoice line for security refund amount and link with created invoice
                    inv_line_res = {
                        'name': "Refund security amount for the rental order %r " % rec.rental_sequence,
                        'origin': rec.rental_sequence,
                        'account_id': account.id,
                        'price_unit': rec.total_deposit_security_amount,
                        'quantity': 1,
                        'product_id': security_refund_product_obj.id or False,
                        'invoice_line_tax_ids': [(6, 0, security_refund_product_obj.taxes_id.ids if security_refund_product_obj.taxes_id else [])],
                        'invoice_id': invoice_obj.id
                    }
                    invoice_lines = self.env['account.invoice.line'].create(
                        inv_line_res)
                    return self.button_view_invoice()

    @api.multi
    def button_view_invoice(self):
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
        action['res_id'] = self.mapped('security_refund_invoice_id').ids[0]
        return action

    @api.multi
    def _get_delivered_qty(self):
        self.ensure_one()
        res = super(SaleOrderLine, self)._get_delivered_qty()
        qty = res
        if self.is_rental_order and self.inital_rental_contract_id and self.inital_rental_contract_id.stock_move_ids:
            qty = 0.0
            for move in self.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped):
                if move.id in self.inital_rental_contract_id.stock_move_ids.ids:
                    if move.location_dest_id.usage == "customer":
                        if not move.origin_returned_move_id:
                            qty += move.product_uom._compute_quantity(
                                move.product_uom_qty, self.product_uom)
                    elif move.location_dest_id.usage != "customer" and move.to_refund:
                        qty -= move.product_uom._compute_quantity(
                            move.product_uom_qty, self.product_uom)
        return qty
