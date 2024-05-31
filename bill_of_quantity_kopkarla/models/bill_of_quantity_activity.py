from odoo import models, fields, api, _


class bill_quantity_line_activity(models.Model):
    _name = 'bill.quantity.line.activity'
    _description = 'Bill Of Quantity Line Activity'

    boq_line_id = fields.Many2one('bill.quantity.line', 'BoQ Line', ondelete='cascade')
    notes = fields.Text('Notes')
