# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ast import literal_eval

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    multi_cash_advance = fields.Boolean('Multi Cash Advance', default=True)
    eam_journal_id = fields.Many2one('account.journal', string='Default Expense Journal', domain=lambda self: [('type', '=', 'purchase')])
    ret_journal_id = fields.Many2one('account.journal', string='Default Return Advance Journal', domain=lambda self: [('type', '=', 'cash')])
    default_payment_id = fields.Many2one('account.journal', string='Default Payment Journal', domain=lambda self: ['|',('type', '=', 'bank'),('type', '=', 'cash')])
    default_expense_partner_id = fields.Many2one('res.partner', string='Default Expense Partner', domain=lambda self: [('customer', '=', False),('supplier', '=', False)])

    default_exp_created_sign_by = fields.Many2one('hr.employee', string='Dibuat')
    default_exp_checked_sign_by = fields.Many2one('hr.employee', string='Diperiksa')
    default_exp_known_sign_by = fields.Many2one('hr.employee', string='Mengetahui')
    default_exp_done_sign_by = fields.Many2one('hr.employee', string='Dilaksanakan')
    default_exp_management_sign_by = fields.Many2one('hr.employee', string='Pengurus')

    default_product_unbudget = fields.Many2one('product.product', string='Product Un-Budget')

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        # eam_journal_id = literal_eval(get_param('eam_journal_id', default='False'))
        # if eam_journal_id and not self.env['account.journal'].sudo().browse(eam_journal_id).exists():
        #     eam_journal_id = False
        # ret_journal_id = literal_eval(get_param('ret_journal_id', default='False'))
        # if ret_journal_id and not self.env['account.journal'].sudo().browse(ret_journal_id).exists():
        #     ret_journal_id = False
        # default_payment_id = literal_eval(get_param('default_payment_id', default='False'))
        # if default_payment_id and not self.env['account.journal'].sudo().browse(default_payment_id).exists():
        #     default_payment_id = False

        res.update(
            multi_cash_advance = get_param('multi_cash_advance'),
            eam_journal_id = literal_eval(get_param('eam_journal_id', default='False')), # eam_journal_id,
            ret_journal_id = literal_eval(get_param('ret_journal_id', default='False')), # ret_journal_id,
            default_payment_id = literal_eval(get_param('default_payment_id', default='False')),
            default_expense_partner_id = literal_eval(get_param('default_expense_partner_id', default='False')),
            default_exp_created_sign_by = literal_eval(get_param('default_exp_created_sign_by', default='False')),
            default_exp_checked_sign_by = literal_eval(get_param('default_exp_checked_sign_by', default='False')),
            default_exp_known_sign_by = literal_eval(get_param('default_exp_known_sign_by', default='False')),
            default_exp_done_sign_by = literal_eval(get_param('default_exp_done_sign_by', default='False')),
            default_exp_management_sign_by = literal_eval(get_param('default_exp_management_sign_by', default='False')),
            default_product_unbudget = literal_eval(get_param('default_product_unbudget', default='False')),
        )
        # res = super(ResConfigSettings, self).get_values()
        # params = self.env['ir.config_parameter'].sudo()
        # res.update(multi_cash_advance=params.get_param('multi_cash_advance'))
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('multi_cash_advance', self.multi_cash_advance)
        set_param('eam_journal_id', self.eam_journal_id.id)
        set_param('ret_journal_id', self.ret_journal_id.id)
        set_param('default_payment_id', self.default_payment_id.id)
        set_param('default_expense_partner_id', self.default_expense_partner_id.id)
        set_param('default_exp_created_sign_by', self.default_exp_created_sign_by.id)
        set_param('default_exp_checked_sign_by', self.default_exp_checked_sign_by.id)
        set_param('default_exp_known_sign_by', self.default_exp_known_sign_by.id)
        set_param('default_exp_done_sign_by', self.default_exp_done_sign_by.id)
        set_param('default_exp_management_sign_by', self.default_exp_management_sign_by.id)
        set_param('default_product_unbudget', self.default_product_unbudget.id)
