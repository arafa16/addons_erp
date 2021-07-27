from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PaymentJournal(models.Model):
    _inherit = "payment.journal"

    partner_bank_id = fields.Many2one('res.partner.bank', string='Bank', domain="[('partner_id', '=', partner_id)]")
    # state = fields.Selection(selection_add=[('confirm', 'Confirmed')])
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('sent', 'Sent'), ('posted', 'Posted'),
                              # ('reconciled', 'Reconciled'),
                              ('cancelled', 'Cancelled')], readonly=True, default='draft', copy=False, string="Status")

    @api.multi
    @api.onchange('partner_id')
    def onchange_area_id(self):
        self.partner_bank_id = False
        if self.partner_id:
            partner_bank_id = self.env['res.partner.bank'].search([('partner_id', '=', self.partner_id.id)])
            if partner_bank_id:
                self.partner_bank_id = partner_bank_id[0].id
        return {
            'domain': {'partner_bank_id': [('partner_id', '=', self.partner_id.id)]},
        }

    @api.multi
    def confirm(self):
        if self.filtered(lambda payment: payment.amount == 0):
            raise UserError(_("Belum ada pembayaran. Masukan pembayaran di Balance to Pay."))

        self.line_ids.filtered(lambda line: line.paying_amt == 0).unlink()
        self.write({'state': 'confirm'})

    @api.multi
    def action_draft(self):
        if self.filtered(lambda payment: payment.state not in ['confirm', 'cancelled']):
            raise UserError(_("Payment must be cancelled in order to reset it to draft."))
        # go from canceled state to draft state
        self.write({'state': 'draft'})