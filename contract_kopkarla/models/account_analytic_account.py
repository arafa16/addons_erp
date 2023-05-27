from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    note = fields.Text('Terms and conditions', compute='_get_sales_attribute')
    penandatangan  = fields.Many2one('hr.employee', compute='_get_sales_attribute')
    pegawai_ttd = fields.Many2one('hr.employee', compute='_get_sales_attribute')

    @api.multi
    @api.depends('code')
    def _get_sales_attribute(self):
        for analytic in self:
            sale = self.env['sale.order'].sudo().search([('name','=',analytic.code)], limit=1)
            analytic.note = sale.note
            analytic.pegawai_ttd = sale.pegawai_ttd
            if sale.required5 == True:
                analytic.penandatangan = sale.penandatangan5.id
            elif sale.required4 == True:
                analytic.penandatangan = sale.penandatangan4.id
            elif sale.required3 == True:
                analytic.penandatangan = sale.penandatangan3.id
            elif sale.required2 == True:
                analytic.penandatangan = sale.penandatangan2.id
            else:
                analytic.penandatangan = sale.penandatangan1.id

    @api.model
    def _prepare_invoice_line(self, line, invoice_id):
        invoice_line = self.env['account.invoice.line'].new({
            'invoice_id': invoice_id,
            'product_id': line.product_id.id,
            'quantity': line.quantity,
            'uom_id': line.uom_id.id,
            'discount': line.discount,
        })
        # Get other invoice line values from product onchange
        invoice_line._onchange_product_id()
        invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)

        if invoice_line.product_id.asset_category_id.account_asset_id:
            accounts = invoice_line.product_id.product_tmpl_id.get_product_accounts(invoice_line.invoice_id.fiscal_position_id)
            if invoice_line.invoice_id.type in ('out_invoice', 'out_refund'):
                invoice_line_vals['account_id'] = accounts['income'].id

        # Insert markers
        contract = line.analytic_account_id
        lang_obj = self.env['res.lang']
        lang = lang_obj.search(
            [('code', '=', contract.partner_id.lang)])
        date_format = lang.date_format or '%m/%d/%Y'
        name = self._insert_markers(line, date_format)
        invoice_line_vals.update({
            'name': name,
            # 'account_analytic_id': contract.id,
            'account_analytic_id': contract.parent_id.id,
            'cost_center_id': contract.sale_order_id.cost_center_id.id,
            'price_unit': line.price_unit,
        })
        return invoice_line_vals
