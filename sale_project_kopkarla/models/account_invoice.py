from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_id = fields.Many2one('sale.order', string='Sales Order')

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        exp_acc = self._get_sales_expense()
        if exp_acc:
            for dict_data in res:
                # invl_id = dict_data.get('invl_id')
                # line = self.env['account.invoice.line'].browse(invl_id)
                if 'invl_id' not in dict_data:
                    product_id = dict_data['product_id']
                    product = self.env['product.product'].sudo().browse(product_id)
                    acc_id = self._replace_expense_account(dict_data['account_id'], product, exp_acc)
                    if acc_id:
                        dict_data['account_id'] = acc_id
        return res

    def _get_sales_expense(self):
        sale_id = self.env['sale.order'].sudo().search([('name', '=', self.origin)])
        if sale_id:
            if sale_id.jenis_so in ('Project', 'datacom'):
                return sale_id.proj_type.project_account_id.id
        return False

    def _replace_expense_account(self, acc_id, product, exp_acc):
        if product.type == 'product' and product.valuation == 'real_time':
            accounts = product.product_tmpl_id.get_product_accounts()
            # debit account dacc will be the output account
            out_acc = accounts['stock_output'].id
            # credit account cacc will be the expense account
            in_acc = accounts['stock_input'].id
            if acc_id not in (out_acc, in_acc):
                return exp_acc
        return False