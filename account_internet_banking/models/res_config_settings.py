from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    default_batch_payment1_by = fields.Many2one('hr.employee', string='Approver 1')
    default_batch_payment2_by = fields.Many2one('hr.employee', string='Approver 2')

    @api.multi
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(default_batch_payment1_by=int(params.get_param('default_batch_payment1_by')),
                   default_batch_payment2_by=int(params.get_param('default_batch_payment2_by')),
                   )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('default_batch_payment1_by', self.default_batch_payment1_by.id)
        set_param('default_batch_payment2_by', self.default_batch_payment2_by.id)
