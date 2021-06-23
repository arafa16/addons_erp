from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    invoice_amount = fields.Monetary(string='Invoice Amount', readonly=True, compute='_compute_invoice_amount')
    residual_amount = fields.Monetary(string='Residual Amount', readonly=True, compute='_compute_invoice_amount')

    @api.depends('order_line.invoice_lines.invoice_id')
    def _compute_invoice_amount(self):
        for order in self:
            # invoices = self.env['account.invoice']
            invoices_amount = 0
            for line in order.order_line:
                # invoices |= line.invoice_lines.mapped('invoice_id')
                for inv_line in line.invoice_lines:
                    invoices_amount += inv_line.price_total
            # order.invoice_ids = invoices
            order.invoice_amount = invoices_amount
            order.residual_amount = order.amount_total - invoices_amount

    # @api.multi
    # def write(self, values):
    #     res = super(PurchaseOrder, self).write(values)
    #     if 'invoice_status' in values and values['invoice_status'] == 'to invoice':
    #         lines = self.env['purchase.order.line'].search([('order_id', '=', values['id'])])
    #     return res

    @api.multi
    def action_set_waiting_bills(self):
        for purch in self:
            purch.invoice_status = 'to invoice'
            for line in purch.order_line:
                line.qty_to_invoice = line.product_qty - line.qty_invoiced

    @api.multi
    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()
        journal_domain = [
            ('type', '=', 'purchase'),
            ('company_id', '=', self.company_id.id),
            # ('currency_id', '=', self.currency_id.id),
        ]
        journal_id = self.env['account.journal'].search(journal_domain, limit=1).id
        # journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
        if not journal_id:
            raise UserError(_('Please define an accounting purchase journal for this company.'))
        invoice_vals = {
            'name': self.partner_ref or '',
            'origin': self.name,
            'type': 'in_invoice',
            'account_id': self.partner_id.property_account_payable_id.id,
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.dest_address_id.id,
            'journal_id': journal_id,
            'currency_id': self.currency_id.id,
            'comment': self.notes,
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id or self.partner_id.property_account_position_id.id,
            'company_id': self.company_id.id,
            'user_id': self.create_uid.id, # self.user_id and self.user_id.id,
            # 'team_id': self.team_id.id
        }
        return invoice_vals

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        invoices_origin = {}
        invoices_name = {}

        for order in self:
            group_key = order.id if grouped else (order.partner_id.id, order.currency_id.id)
            for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                    continue
                if group_key not in invoices:
                    inv_data = order._prepare_invoice()
                    invoice = inv_obj.create(inv_data)
                    references[invoice] = order
                    invoices[group_key] = invoice
                    invoices_origin[group_key] = [invoice.origin]
                    invoices_name[group_key] = [invoice.name]
                elif group_key in invoices:
                    if order.name not in invoices_origin[group_key]:
                        invoices_origin[group_key].append(order.name)
                    if order.partner_ref and order.partner_ref not in invoices_name[group_key]:
                        invoices_name[group_key].append(order.client_order_ref)

                if line.qty_to_invoice > 0:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                elif line.qty_to_invoice < 0 and final:
                    line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoices[group_key]] |= order

        for group_key in invoices:
            invoices[group_key].write({'name': ', '.join(invoices_name[group_key]),
                                       'origin': ', '.join(invoices_origin[group_key])})

        if not invoices:
            raise UserError(_('There is no invoiceable line.'))

        for invoice in invoices.values():
            invoice.compute_taxes()
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoiceable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_total < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                values={'self': invoice, 'origin': references[invoice]},
                subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    qty_to_invoice = fields.Float(
        compute='_get_to_invoice_qty', string='To Invoice', store=True, readonly=True,
        digits=dp.get_precision('Product Unit of Measure'))
    is_downpayment = fields.Boolean(
        string="Is a down payment", help="Down payments are made when creating invoices from a purchase order."
        " They are not copied when duplicating a purchase order.")

    @api.depends('qty_invoiced', 'qty_received', 'product_qty', 'order_id.state')
    def _get_to_invoice_qty(self):
        for line in self:
            if line.order_id.state in ['purchase', 'done']:
                if line.product_id.purchase_method == 'purchase':
                    line.qty_to_invoice = line.product_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_received - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        # res = {}
        account = self.env['account.account']
        if self.product_id.type == 'product':
            accounts = self.product_id.product_tmpl_id.get_product_accounts()
            if accounts['stock_input']:
                account = accounts['stock_input']
                if not account:
                    raise UserError(_('Please define stock input account for this product: "%s" (id:%d) - or for its category: "%s".') %
                        (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))
        else:
            bid = self.env['purchase.requisition'].sudo().browse(self.order_id.requisition_id.id)
            req = self.env['sprogroup.purchase.request'].sudo().search([('nomor_bidding', '=', bid.id)])
            req_line = self.env['sprogroup.purchase.request.line'].sudo().search([('request_id', '=', req.id), ('product_id', '=', self.product_id.id)], limit=1)
            if req_line:
                account = req_line.account_id
            else:
                account = self.product_id.property_account_expense_id or self.product_id.categ_id.property_account_expense_categ_id
            if not account:
                raise UserError(_('Please define expense account for this product: "%s" (id:%d) - or for its category: "%s".') %
                    (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        if not account.id:
            raise UserError(
                _('Please define stock input account for this product: "%s" (id:%d) - or for its category: "%s".') %
                (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            # 'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            # 'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.taxes_id.ids)],
            'cost_center_id': self.order_id.cost_center_id.id,
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """ Create an invoice line. The quantity to invoice can be positive (invoice) or negative (refund).
            :param invoice_id: integer
            :param qty: float quantity to invoice
            :returns recordset of account.invoice.line created
        """
        invoice_lines = self.env['account.invoice.line']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'purchase_line_id': line.id})
                invoice_lines |= self.env['account.invoice.line'].create(vals)
        return invoice_lines
