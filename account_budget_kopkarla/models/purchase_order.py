from odoo import models, fields, api, _

from odoo.exceptions import ValidationError
from odoo.exceptions import UserError, AccessError
from odoo.tools.float_utils import float_is_zero, float_compare

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # @api.multi
    # def button_confirm(self):
    #     if not self.analytic_account_id :
    #         res = super(PurchaseOrder, self).button_confirm()
    #         return res
    #     else :
    #         for line in self.order_line:
    #             amount = self.currency_id.with_context(date=self.date_order or fields.Date.today()).compute(
    #                 line.price_subtotal, line.company_id.currency_id)
    #             budget_lines = self.env['crossovered.budget.lines'].sudo().search([('date_from', '<=', self.date_order),
    #                                                                                ('date_to', '>=', self.date_order),
    #                                                                                ('analytic_account_id', '=', line.account_analytic_id.id),
    #                                                                                ('cost_center_id', '=', line.cost_center_id.id),
    #                                                                                ('company_id', '=', self.company_id.id)])
    #             for budget_line in budget_lines:
    #                 if line.account_id.id in budget_line.general_budget_id.account_ids.ids:
    #                     if  abs(budget_line.planned_amount) < abs(budget_line.commitment_amount - amount):
    #                         if budget_line.restrict_allow == 'restrict':
    #                             raise ValidationError(
    #                                              _("Don't have enough available amount for %s .")%self.analytic_account_id.name)
    #     return super(PurchaseOrder, self).button_confirm()

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res['cost_center_id'] = self.cost_center_id.id
        res['analytic_account_id'] = self.analytic_account_id.id
        return res

    @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        self.mapped('order_line')._create_analytic_line()
        return res

    @api.multi
    def button_cancel(self):
        """ Revert analytic line created at order confirmation.
        Do not create a revert line for orders that were not confirmed.
        """
        order_lines_to_reverse = self.filtered(
            lambda order: order.state == 'purchase').mapped('order_line')
        res = super(PurchaseOrder, self).button_cancel()
        order_lines_to_reverse._create_analytic_line(reverse=True)
        return res

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        if not self.requisition_id:
            return

        requisition = self.requisition_id
        if self.partner_id:
            partner = self.partner_id
        else:
            partner = requisition.vendor_id
        payment_term = partner.property_supplier_payment_term_id
        currency = partner.property_purchase_currency_id or requisition.company_id.currency_id

        FiscalPosition = self.env['account.fiscal.position']
        fpos = FiscalPosition.get_fiscal_position(partner.id)
        fpos = FiscalPosition.browse(fpos)

        self.partner_id = partner.id
        self.fiscal_position_id = fpos.id
        self.payment_term_id = payment_term.id
        self.company_id = requisition.company_id.id
        self.currency_id = currency.id
        if not self.origin or requisition.name not in self.origin.split(', '):
            if self.origin:
                if requisition.name:
                    self.origin = self.origin + ', ' + requisition.name
            else:
                self.origin = requisition.name
        self.notes = requisition.description
        self.date_order = requisition.date_end or fields.Datetime.now()
        self.picking_type_id = requisition.picking_type_id.id
        self.cost_center_id = requisition.cost_center_id
        self.analytic_account_id = requisition.account_analytic_id

        if requisition.type_id.line_copy != 'copy':
            return

        # Create PO lines if necessary
        order_lines = []
        for line in requisition.line_ids:
            # Compute name
            product_lang = line.product_id.with_context({
                'lang': partner.lang,
                'partner_id': partner.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            # Compute taxes
            if fpos:
                taxes_ids = fpos.map_tax(line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id)).ids
            else:
                taxes_ids = line.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == requisition.company_id).ids

            # Compute quantity and price_unit
            if line.product_uom_id != line.product_id.uom_po_id:
                product_qty = line.product_uom_id._compute_quantity(line.product_qty, line.product_id.uom_po_id)
                price_unit = line.product_uom_id._compute_price(line.price_unit, line.product_id.uom_po_id)
            else:
                product_qty = line.product_qty
                price_unit = line.price_unit

            if requisition.type_id.quantity_copy != 'copy':
                product_qty = 0

            # Compute price_unit in appropriate currency
            if requisition.company_id.currency_id != currency:
                price_unit = requisition.company_id.currency_id.compute(price_unit, currency)

            # Create PO line
            order_line_values = line._prepare_purchase_order_line(
                name=name, product_qty=product_qty, price_unit=price_unit,
                taxes_ids=taxes_ids)
            order_lines.append((0, 0, order_line_values))
        self.order_line = order_lines


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    account_id = fields.Many2one('account.account', string='Account', compute='_get_invoice_line_account', store=True)

    @api.one
    @api.depends('product_id')
    def _get_invoice_line_account(self):
        for line in self:
            account_id = False
            if line.order_id.requisition_id.id:
                account_id = line.order_id.requisition_id.nomor_pr.line_ids.filtered(lambda x: x.product_id == line.product_id).mapped('account_id')[0].id
            if not account_id and self.product_id:
                accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
                if self.product_id.type == 'product':
                    account_id = accounts_data['stock_input'].id
                else:
                    account_id = accounts_data['expense'].id
            self.account_id = account_id

    def _prepare_analytic_line(self, reverse=False):
        planned_amount_sign = self._get_settings_planned_amount_sign()
        sign = reverse and -1 or 1
        order = self.order_id
        # Get default account used to generate supplier invoice
        account = self.product_id.product_tmpl_id. \
            get_product_accounts().get('expense')
        return {
            'name': self.name,
            'product_id': self.product_id.id,
            'account_id': self.account_analytic_id.id,
            'unit_amount': sign * self.product_qty,
            'product_uom_id': self.product_uom.id,
            'amount': planned_amount_sign * sign * order.currency_id.
            with_context(date=order.date_order).compute(
                self.price_subtotal, order.company_id.currency_id),
            'commitment_account_id': account and account.id,
            'ref': self.order_id.name,
            'user_id': self._uid,
        }

    @api.one
    def _create_analytic_line(self, reverse=False):
        if self.account_analytic_id:
            vals = self._prepare_analytic_line(reverse=reverse)
            self.env['account.analytic.line'].create(vals)

    @api.model
    def _get_settings_planned_amount_sign(self):
        res = self.env['res.config.settings'].get_values()
        return res.get('planned_amount_sign') == 'positive' and 1 or -1

    @api.multi
    def _prepare_stock_moves(self, picking):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        for move in self.move_ids.filtered(lambda x: x.state != 'cancel' and not x.location_dest_id.usage == "supplier"):
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method='HALF-UP')
        template = {
            'name': (self.name or '')[:2000],
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'date': self.order_id.date_approve,
            'date_expected': self.date_planned,
            'location_id': self.order_id.partner_id.property_stock_supplier.id,
            'location_dest_id': self.order_id._get_destination_location(),
            'picking_id': picking.id,
            'partner_id': self.order_id.dest_address_id.id,
            'move_dest_ids': [(4, x) for x in self.move_dest_ids.ids],
            'state': 'draft',
            'purchase_line_id': self.id,
            'company_id': self.order_id.company_id.id,
            'price_unit': price_unit,
            'picking_type_id': self.order_id.picking_type_id.id,
            'group_id': self.order_id.group_id.id,
            'origin': self.order_id.name,
            'route_ids': self.order_id.picking_type_id.warehouse_id and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])] or [],
            'warehouse_id': self.order_id.picking_type_id.warehouse_id.id,
            'cost_center_id': self.cost_center_id.id,
            'analytic_account_id': self.account_analytic_id.id,
        }
        diff_quantity = self.product_qty - qty
        if float_compare(diff_quantity, 0.0,  precision_rounding=self.product_uom.rounding) > 0:
            quant_uom = self.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if self.product_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = self.product_uom._compute_quantity(diff_quantity, quant_uom, rounding_method='HALF-UP')
                template['product_uom'] = quant_uom.id
                template['product_uom_qty'] = product_qty
            else:
                template['product_uom_qty'] = diff_quantity
            res.append(template)
        return res

class AccountInvoice_Inherit(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def invoice_validate(self):
        budget_control = self.env['ir.config_parameter'].sudo().get_param('allow_budget_ledger_control')
        if budget_control:
            if self.type == 'in_invoice' :
                po_res = self.env['purchase.order'].search([('name','=',self.origin)])
                if po_res :
                    res = super(AccountInvoice_Inherit, self).invoice_validate()
                    return res

                analytic_budget = {}
                for line in self.invoice_line_ids :
                    if line.account_analytic_id.id not in analytic_budget :
                        analytic_budget[line.account_analytic_id.id] = line.price_subtotal
                    else :
                        analytic_budget[line.account_analytic_id.id] = analytic_budget[line.account_analytic_id.id] + line.price_subtotal
                for account in analytic_budget :
                    if account :
                        date_check = fields.Date.today()
                        if self.date_invoice :
                            date_check = self.date_invoice
                        budget_line = self.env['crossovered.budget.lines'].sudo().search([('date_from','<=',date_check),
                                                                                ('date_to','>=',date_check),
                                                                                ('analytic_account_id','=',account)
                                                                                ],limit=1)
                        amount = self.currency_id.with_context(date=date_check).compute(analytic_budget[account], self.company_id.currency_id)
                        if budget_line :
                            if budget_line.crossovered_budget_id.state in ['draft','cancel'] :
                                raise ValidationError(
                                                _("Unable to find budget for %s , please contact to the budget manager.")%budget_line.analytic_account_id.name)
                            if budget_line.restrict_allow_ledger == 'restrict':
                                if  budget_line.planned_amount < abs(budget_line.practical_amount + amount) :
                                    raise ValidationError(
                                                    _("Don't have enough available amount for %s.")%budget_line.analytic_account_id.name)
                        else :
                            raise ValidationError(
                                                _("Unable to find budget for %s , please contact to the budget manager.")%budget_line.analytic_account_id.name)
        res = super(AccountInvoice_Inherit, self).invoice_validate()
        return res
