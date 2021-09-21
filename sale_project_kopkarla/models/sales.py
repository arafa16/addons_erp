from odoo import models, fields, api
from odoo.exceptions import UserError


class EnhancedSalesArea(models.Model):
    _inherit = "sale.order"

    partner_invoice_name = fields.Char(string='Customer Invoice', related='partner_invoice_id.name', store=True)
    bast_no = fields.Char(string='BAST No.')
    bast_date = fields.Date(string='BAST Date')
    purchase_count = fields.Integer(string='# of Purchases', compute='_get_purchased', readonly=True)
    purchase_amount = fields.Float(string='# of Purchases', compute='_get_purchased', readonly=True, store=True)
    purchase_ids = fields.Many2many("purchase.order", string='Purchases', compute="_get_purchased", readonly=True, copy=False)
    advance_amount = fields.Float(string='# of Advances', compute='_get_advance', readonly=True, store=True)
    expense_amount = fields.Float(string='# of Expenses', compute='_get_expense', readonly=True, store=True)

    @api.multi
    def convert_to_project(self):
        # super(EnhancedSalesArea, self)
        projid = 0
        cekProj = self.env['project.project'].search([('partner_id', '=', self.partner_shipping_id.id), ('j_project', '=', self.proj_type.id),('nojar', '=', self.nojar)])
        if len(cekProj) > 0:
            projid = cekProj[0].id
            namaProj = cekProj[0].name
        else:
            if self.nojar == False or self.nojar == "":
                namaProj = self.proj_type.name + " " + self.partner_shipping_id.name
            else:
                namaProj = self.proj_type.name + " " + self.partner_shipping_id.name + " Nojar. " + self.nojar

            isiProject = {
                'active': True,
                'alias_contact': 'everyone',
                'alias_id': False,
                'alias_name': False,
                'analytic_account_id': False,
                'label_tasks': 'Tasks',
                'name': namaProj,
                'partner_id': self.partner_shipping_id.id,
                'privacy_visibility': 'employees',
                'resource_calendar_id': False,
                'sequence': 10,
                'subtask_project_id': False,
                'user_id': self._uid,
                'type_ids': False,
                'j_project': self.proj_type.id,
                'nojar': self.nojar
            }
            projo = self.env['project.project'].create(isiProject)
            projid = projo.id

        bb = self.env['project.task.type'].search([('jenis_pek', 'in', self.pek_type.id)])
        stageid = False
        stageproj = []
        ke7 = 0
        for cc in bb:
            if ke7 == 0:
                stageid = cc.id
            ke7 = ke7 + 1
            adac = False
            for cfr in cc.project_ids:
                if cfr.id == projid:
                    adac = True
            if adac == False:
                valsa = {}
                valsa['project_ids'] = []
                keong = []
                keong.append(4)
                keong.append(projid)
                valsa['project_ids'].append(keong)
                cc.write(valsa)

        tagid = []
        isitag = []
        isitag.append(6)
        isitag.append(False)
        isi2 = []
        isitag.append(isi2)
        tagid.append(isitag)
        if self.nojar == False or self.nojar == "":
            namaTask = self.pek_type.name + " " + self.proj_type.name + " " + self.partner_shipping_id.name
        else:
            namaTask = self.pek_type.name + " " + self.proj_type.name + " " + self.partner_shipping_id.name + " Nojar. " + self.nojar

        # ------------------- mark by hypur, 22 May 2021 ------------------------------------
        # Jangan create new analytic account
        # projAnalytic = self.env['account.analytic.account'].search(
        #     [('name', '=', namaProj)], limit=1)
        # if len(projAnalytic) > 0:
        #     projAnalyticId = projAnalytic[0].id
        #
        #     recAnalyticAccount = {
        #         'name': namaTask,
        #         'parent_id': projAnalyticId,
        #     }
        #     task_analytic = self.env['account.analytic.account'].create(recAnalyticAccount)
        #     projAnalytic.parent_id = self.analytic_account_id.id
        # -----------------------------------------------------------------------------------

        isiTask = {
            'active': True,
            'company_id': self.company_id.id,
            'description': '<p><br></p>',
            'kanban_state': 'normal',
            'name': namaTask,
            'parent_id': False,
            'partner_id': self.partner_shipping_id.id,
            'cost_center_id': self.cost_center_id.id,
            'analytic_account_id': self.analytic_account_id.id, #task_analytic[0].id,
            'priority': '0',
            'project_id': projid,
            'sale_order_id': self.id,
            'stage_id': stageid,
            'user_id': self._uid,
            'kanban_baru': 'A'
        }
        self.task_id = self.env['project.task'].create(isiTask)

    # @api.depends('state', 'order_line.invoice_status')
    @api.multi
    def _get_purchased(self):
        for order in self:
            purchase_request_ids = self.env['sprogroup.purchase.request'].sudo().search([('salesorder_id', '=', order.id)])
            po_ids = []
            for pr in purchase_request_ids:
                for po in pr.nomor_po_m2o:
                    if po.id not in po_ids:
                        po_ids.append(po.id)
            purchase_order = self.env['purchase.order'].sudo().search([('id', 'in', po_ids), ('state', '!=', 'cancel')])
            po_amount = po_count = 0
            for po in purchase_order:
                po_amount += po.amount_untaxed
                po_count += 1

            order.update({
                'purchase_count': po_count,
                'purchase_amount': po_amount,
                'purchase_ids': po_ids,
            })

    @api.multi
    def _get_advance(self):
        for order in self:
            adv_amount = 0
            for adv in self.env['hr.advance'].sudo().search([('order_id', '=', order.id),('state', '=', 'paid')]):
                adv_amount += adv.total_amount_expense

            order.update({
                'advance_amount': adv_amount,
            })

    @api.multi
    def _get_expense(self):
        for order in self:
            exp_amount = 0
            for exp in self.env['hr.expense.sheet'].sudo().search([('order_id', '=', order.id),('state', '=', 'done')]):
                exp_amount += exp.expense_amount

            order.update({
                'expense_amount': exp_amount,
            })

    @api.multi
    def action_view_purchase(self):
        purchases = self.mapped('purchase_ids')
        action = self.env.ref('purchase.purchase_form_action').read()[0]
        if len(purchases) > 1:
            action['domain'] = [('id', 'in', purchases.ids)]
        elif len(purchases) == 1:
            action['views'] = [(self.env.ref('purchase.purchase_order_form').id, 'form')]
            action['res_id'] = purchases.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def copy(self, default=None):
        new_so = super(EnhancedSalesArea, self).copy(default=default)
        for line in new_so.order_line:
            if not line.product_id.active:
                line.unlink()
        return new_so


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_invoice_line(self, qty):
        self.ensure_one()
        res = {}
        product_id = self.env['ir.config_parameter'].sudo().get_param('sale.default_deposit_product_id')
        if self.order_id.jenis_so in ('Project', 'datacom') and self.product_id.type != 'product' and self.product_id.id != int(product_id):
            account = self.order_id.proj_type.project_income_id
            if not account:
                raise UserError(_('Please define income account for this order type: "%s"') % (self.order_id.jenis_so))
        else:
            account = self.product_id.property_account_income_id or self.product_id.categ_id.property_account_income_categ_id
            if not account:
                raise UserError(_('Please define income account for this product: "%s" (id:%d) - or for its category: "%s".') %
                    (self.product_id.name, self.product_id.id, self.product_id.categ_id.name))

        fpos = self.order_id.fiscal_position_id or self.order_id.partner_id.property_account_position_id
        if fpos:
            account = fpos.map_account(account)

        res = {
            'name': self.name,
            'sequence': self.sequence,
            'origin': self.order_id.name,
            'account_id': account.id,
            'price_unit': self.price_unit,
            'quantity': qty,
            'discount': self.discount,
            'uom_id': self.product_uom.id,
            'product_id': self.product_id.id or False,
            'layout_category_id': self.layout_category_id and self.layout_category_id.id or False,
            'invoice_line_tax_ids': [(6, 0, self.tax_id.ids)],
            'account_analytic_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
        }
        return res