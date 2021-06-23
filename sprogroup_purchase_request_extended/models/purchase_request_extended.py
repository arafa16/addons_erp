# -*- coding: utf-8 -*-
# Copyright 2016 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).

from odoo import api, fields, models, _ , SUPERUSER_ID
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class SprogroupPurchaseRequestExtended(models.Model):
    _inherit = ['sprogroup.purchase.request']


    @api.one
    @api.depends('state')
    def _compute_is_sendmail(self):
#        print ("send_email: State change: ", self.state, self.requested_by.email, self.assigned_to.email)
        if(self.state == 'to_approve'):
            print ("send_email: State change: to_approve", self.state, self.requested_by.email, self.assigned_to.email)
            template = self.env.ref('sprogroup_purchase_request_extended.purchase_request_email_template')
            self.env['mail.template'].browse(template.id).send_mail(self.id, force_send=True)
            self.is_sendmail = True
        elif (self.state == 'leader_approved'):
            print ("send_email: State change: leader_approved", self.state, self.requested_by.email, self.assigned_to.email)
            self.is_sendmail = True
        elif (self.state == 'manager_approved'):
            print ("send_email: State change: manager_approved", self.state, self.requested_by.email, self.assigned_to.email)
            self.is_sendmail = True
        elif (self.state == 'rejected'):
            print ("send_email: State change: rejected", self.state, self.requested_by.email, self.assigned_to.email)
            self.is_sendmail = True
        elif (self.state == 'done'):
            print ("send_email: State change: done", self.state, self.requested_by.email, self.assigned_to.email)
            self.is_sendmail = True
        else:
            self.is_sendmail = False

    is_sendmail = fields.Boolean(string="Is send mail", compute="_compute_is_sendmail", store=True)
#
#    @api.multi
#    def button_to_approve(self):
#        self.write({'state': 'to_approve'})
#        self._compute_is_mailto_approve();
#        return True

