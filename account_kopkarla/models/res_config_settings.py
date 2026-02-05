from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mandatory_faktur = fields.Boolean(string="Mandatory Faktur")
    under_payment_account = fields.Many2one('account.account', string='Underpaid Account')
    over_payment_account = fields.Many2one('account.account', string='Overpaid Account')
    default_bank_transfer_to_id = fields.Many2one('account.journal', string='Default Bank Destination', domain=[('type', 'in', ('bank', 'cash'))])
    default_sign_by_id = fields.Many2one('hr.employee', string='Default Sign By')
    default_created_sign_by = fields.Many2one('hr.employee', string='Dibuat')
    default_checked_sign_by = fields.Many2one('hr.employee', string='Diperiksa')
    default_disetujui_sign_by = fields.Many2one('hr.employee', string='Disetujui')
    default_known_sign_by = fields.Many2one('hr.employee', string='Mengetahui')
    default_done_sign_by = fields.Many2one('hr.employee', string='Dilaksanakan')
    default_management_sign_by = fields.Many2one('hr.employee', string='Pengurus')
    default_journal_prepair_by = fields.Many2one('hr.employee', string='Journal Prepared By')
    default_journal_approve_by = fields.Many2one('hr.employee', string='Journal Approved By')

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(mandatory_faktur=params.get_param('mandatory_faktur'),
                   under_payment_account=int(params.get_param('under_payment_account')),
                   over_payment_account=int(params.get_param('over_payment_account')),
                   default_bank_transfer_to_id=int(params.get_param('default_bank_transfer_to_id')),
                   default_sign_by_id=int(params.get_param('default_sign_by_id')),
                   default_created_sign_by=int(params.get_param('default_created_sign_by')),
                   default_checked_sign_by=int(params.get_param('default_checked_sign_by')),
                   default_disetujui_sign_by=int(params.get_param('default_disetujui_sign_by')),
                   default_known_sign_by=int(params.get_param('default_known_sign_by')),
                   default_done_sign_by=int(params.get_param('default_done_sign_by')),
                   default_management_sign_by=int(params.get_param('default_management_sign_by')),
                   default_journal_prepair_by=int(params.get_param('default_journal_prepair_by')),
                   default_journal_approve_by=int(params.get_param('default_journal_approve_by')),
                   )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('mandatory_faktur', self.mandatory_faktur)
        set_param('under_payment_account', self.under_payment_account.id)
        set_param('over_payment_account', self.over_payment_account.id)
        set_param('default_bank_transfer_to_id', self.default_bank_transfer_to_id.id)
        set_param('default_sign_by_id', self.default_sign_by_id.id)
        set_param('default_created_sign_by', self.default_created_sign_by.id)
        set_param('default_checked_sign_by', self.default_checked_sign_by.id)
        set_param('default_disetujui_sign_by', self.default_disetujui_sign_by.id)
        set_param('default_known_sign_by', self.default_known_sign_by.id)
        set_param('default_done_sign_by', self.default_done_sign_by.id)
        set_param('default_management_sign_by', self.default_management_sign_by.id)
        set_param('default_journal_prepair_by', self.default_journal_prepair_by.id)
        set_param('default_journal_approve_by', self.default_journal_approve_by.id)
