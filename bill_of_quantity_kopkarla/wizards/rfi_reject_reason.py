from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RFIRejection(models.TransientModel):
    _name = 'bill.quantity.reject'
    _description = 'RFI Rejection'

    bill_quantity_line_id = fields.Many2one('bill.quantity.line', string='BoQ Line', ondelete='set null', index=True)
    reject_reason = fields.Char(string='Reason', required=1)

    @api.multi
    def execute(self):
        self.bill_quantity_line_id.update({
            'reject_reason': self.reject_reason,
            'state': 'reject'
        })
        subject = 'Reject RFI'
        body = """<b>RFI Rejected</b>
                  <br/>%s""" % (self.reject_reason)
        self.env['mail.message'].create({
            'subject': subject,
            'body': body,
            'model': 'bill.quantity.line',
            'res_id': self.bill_quantity_line_id.id,
            'message_type': 'notification',
            'subtype_id': 1,
        })
