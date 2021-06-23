from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EnhancedHelpdeskTabel(models.Model):
    _name = 'enhanced.helpdesk'
    _inherit = ['mail.thread']

    name = fields.Char(string='Title Request')
    pegawai_id = fields.Many2one('res.users', string='User Request', default=lambda self: self._uid)
    approval_1 = fields.Many2one('res.users', string='Approval Request')
    prioritas = fields.Selection([('low', 'Low'),('middle', 'Middle'),('hight', 'Hight'),('Immediately', 'Immediately')], string='Priority Level', default='low')
    state = fields.Selection([('draft', 'Draft'),('state1', 'Request Approval'),('state2', 'Request Approved'),('state3', 'Developer Received'),('state4', 'Reject'),('state5', 'Done'),('state6', 'Close')], string='Status', default='draft',track_visibility='onchange')
    permintaan = fields.Html(string='Permintaan')
    tindaklanjut = fields.Html(string='Tindak Lanjut')
    responseUser = fields.Html(string='Response User')
    terkait = fields.Many2one('enhanced.helpdesk', string='Helpdesk Terkait')

    @api.multi
    def test_function(self):
        aa = 4
        raise UserError('Nothing Function to be test')

    def action_user_backtodeveloper(self):
        if self._uid == self.approval_1.id:
            self.state = 'state3'
        else:
            raise UserError('Access Denied')
    
    def action_user_close(self):
        if self._uid == self.approval_1.id:
            self.state = 'state6'
        else:
            raise UserError('Access Denied')

    def action_developer_receive(self):
        self.message_post(body="Request received by Developer")
        self.state = 'state3'

    def action_developer_done(self):
        self.message_post(body="Request done by Developer")
        self.state = 'state5'
    
    def action_developer_reopen(self):
        idusr = self._uid
        getusrs = self.env['res.users'].browse(idusr)
        self.message_post(body="Re-Open By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")    
        self.state = 'draft'

    def action_developer_rejected(self):
        self.message_post(body="Requesting Rejected By Developer")
        self.state = 'state4'

    def action_approved(self):
        if self._uid == self.approval_1.id:
            self.state = 'state2'
        else:
            raise UserError('Access Denied.')

    def action_rejected(self):
        if self._uid == self.approval_1.id:
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Requesting Rejected By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")    
            self.state = 'state4'
        else:
            raise UserError('Access Denied.')
    
    def set_to_approval(self):
        getmail = self.sudo().env['ir.mail_server'].search([('sequence','<=',10)])
        sendermail = ''
        if len(getmail) > 0:
            sendermail = getmail[0].smtp_user
        mailto =self.approval_1.email
        template_browse = self.sudo().env['mail.template'].search([('name','=','template_helpdesk')])
        if template_browse.id != False:
            base_url = self.sudo().env['ir.config_parameter'].get_param('web.base.url')
            base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
            self.linktracker = base_url
            kk = template_browse.generate_email(self.id,fields=None)
            kk['email_to'] = mailto
            kk['email_from'] = sendermail
            kk['res_id'] = False
            mail_obj = self.sudo().env['mail.mail']
            msg_id = mail_obj.create(kk)
            msg_id.send()
        idusr = self._uid
        getusrs = self.env['res.users'].browse(idusr)
        self.message_post(body="Requesting Approval By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>, to "+ self.approval_1.email +"<b><i>("+ self.approval_1.display_name +")</i></b>")
        self.state = 'state1'