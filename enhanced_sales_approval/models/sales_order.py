from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SalesOrder(models.Model):
    _inherit = 'sale.order'
    state = fields.Selection(selection_add_after={'draft': [('spvcheck', 'SPV Check'),('assmancheck', 'Assman Check'),('requestloa', 'Request LoA'),('loaconfirmed', 'LoA Confirmed')]})
    is_spv = fields.Boolean(string='Is Supervisor?', compute='check_spv')
    is_assman = fields.Boolean(string='Is Assman?', compute='check_assman')
    employee_spv = fields.Many2one('hr.employee', string='SPV Check')
    employee_assman = fields.Many2one('hr.employee', string='Assman Check')
    
    penandatangan1 = fields.Many2one('hr.employee', string='Asisten Manager')
    penandatangan2 = fields.Many2one('hr.employee', string='Manager')
    penandatangan3 = fields.Many2one('hr.employee', string='General Manager')
    penandatangan4 = fields.Many2one('hr.employee', string='Pengurus/Direktur')
    penandatangan5 = fields.Many2one('hr.employee', string='Ketua Pengurus')
    penandatangan  = fields.Many2one('hr.employee', compute='_get_penandatangan')

    required1 = fields.Boolean(string='LoA Level 1', compute="setButtoncheck1")
    required2 = fields.Boolean(string='LoA Level 2', compute="setButtoncheck2")
    required3 = fields.Boolean(string='LoA Level 3', compute="setButtoncheck3")
    required4 = fields.Boolean(string='LoA Level 4', compute="setButtoncheck4")
    required5 = fields.Boolean(string='LoA Level 5', compute="setButtoncheck5")
    loa_request = fields.Selection([(1,"Request LoA to Asisten Manager"),(2,"Request LoA to Manager"),(3,"Request LoA to General manager"),(4,"Request LoA to Pengurus/Direktur"),(5,"Request LoA to Ketua Pengurus"),(10,"Done")], string='Status LoA')


    bolehConfirm = fields.Boolean(string='No Var')
    requestLoA = fields.Boolean(string='request LoA ?')
    apvteks = fields.Char(string='Approval')
    linktracker = fields.Char(string='linktracker')
    allowInvoice = fields.Boolean(string='Allow to Create Invoice')

    def _get_penandatangan(self):
        if self.required5 == True:
            self.penandatangan = self.penandatangan5.id
        elif self.required4 == True:
            self.penandatangan = self.penandatangan4.id
        elif self.required3 == True:
            self.penandatangan = self.penandatangan3.id
        elif self.required2 == True:
            self.penandatangan = self.penandatangan2.id
        else:
            self.penandatangan = self.penandatangan1.id

    @api.depends('order_line')
    def setButtoncheck1(self):
        self.required1 = False
        loa1 = self.env['tabel.ttd.sales'].browse(1)
        if loa1.id != False:
            if loa1.batas_atas > 0:
                amount_x = self.amount_total
                if loa1.batas_atas <= amount_x:
                    self.required1 = True
                else:
                    if loa1.batas_bawah <= amount_x:
                        self.required1 = True
    
    @api.depends('order_line')
    def setButtoncheck2(self):
        self.required2 = False
        loa2 = self.env['tabel.ttd.sales'].browse(2)
        if loa2.id != False:
            if loa2.batas_atas > 0:
                amount_x = self.amount_total
                if loa2.batas_atas <= amount_x:
                    self.required2 = True
                else:
                    if loa2.batas_bawah <= amount_x:
                        self.required2 = True
    
    @api.depends('order_line')
    def setButtoncheck3(self):
        self.required3 = False
        loa3 = self.env['tabel.ttd.sales'].browse(3)
        if loa3.id != False:
            if loa3.batas_atas > 0:
                amount_x = self.amount_total
                if loa3.batas_atas <= amount_x:
                    self.required3 = True
                else:
                    if loa3.batas_bawah <= amount_x:
                        self.required3 = True
    
    @api.depends('order_line')
    def setButtoncheck4(self):
        self.required4 = False
        loa4 = self.env['tabel.ttd.sales'].browse(4)
        if loa4.id != False:
            if loa4.batas_atas > 0:
                amount_x = self.amount_total
                if loa4.batas_atas <= amount_x:
                    self.required4 = True
                else:
                    if loa4.batas_bawah <= amount_x:
                        self.required4 = True

    @api.depends('order_line')
    def setButtoncheck5(self):
        self.required5 = False
        loa5 = self.env['tabel.ttd.sales'].browse(5)
        if loa5.id != False:
            if loa5.batas_atas > 0:
                amount_x = self.amount_total
                if loa5.batas_atas <= amount_x:
                    self.required5 = True
                else:
                    if loa5.batas_bawah <= amount_x:
                        self.required5 = True

    def check_spv(self):
        if self._uid == self.employee_spv.user_id.id:
            self.is_spv = True
        else:
            self.is_spv = False
    
    def check_assman(self):
        if self._uid == self.employee_assman.user_id.id:
            self.is_assman = True
        else:
            self.is_assman = False

    def button_action_spv_check(self):
        if self.employee_spv.id == False:
            raise UserError('Supervisior belum diset')
        else:
            tujuan = []
            if self.employee_spv.user_id.email != False:
                tujuan.append(self.employee_spv.user_id.email)
            self._sent_mail(tujuan,'salesorder_quotation_req_spv')
            self.state = 'spvcheck'
    
    def button_action_spv_rejected(self):
        if self.is_spv == True:
            self.state = 'draft'
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Document Rejected SPV Check By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")
        else:
            raise UserError('You dont have access to supervisor')
    
    def button_action_spv_approved(self):
        if self.is_spv == True:
            if self.employee_assman.id == False:
                raise UserError('User Assman belum diset, Cek di tab Reference -> level Of Approva Assman check')
            else:
                tujuan = []
                if self.employee_assman.user_id.email != False:
                    tujuan.append(self.employee_assman.user_id.email)
                self._sent_mail(tujuan,'salesorder_quotation_req_assman')

                idusr = self._uid
                getusrs = self.env['res.users'].browse(idusr)
                self.message_post(body="Document Approved SPV Check By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")
                self.state = 'assmancheck'

                # ----- bypassloa
                if self.jenis_so == 'Project':
                    prosesLoa = True
                    if self.proj_type.id != False and self.ord_type.id != False:
                        if self.proj_type.bypassLoA == True and self.ord_type.bypassLoA == True:
                            prosesLoa = False
                    if prosesLoa and self.pek_type != False:
                        if self.pek_type.bypassLoA == True:
                            prosesLoa = False
                    if not prosesLoa:
                    #     tujuan = []
                    #     if self.required5 == True:
                    #         teksmail = self.penandatangan5.user_id.email
                    #         tail = 'Ketua Pengurus'
                    #         self.loa_request = 5
                    #     if self.required4 == True:
                    #         teksmail = self.penandatangan4.user_id.email
                    #         tail = 'Pengurus/Direktur'
                    #         self.loa_request = 4
                    #     if self.required3 == True:
                    #         teksmail = self.penandatangan3.user_id.email
                    #         tail = 'General Manager'
                    #         self.loa_request = 3
                    #     if self.required2 == True:
                    #         teksmail = self.penandatangan2.user_id.email
                    #         tail = 'Manager'
                    #         self.loa_request = 2
                    #     if self.required1 == True:
                    #         teksmail = self.penandatangan1.user_id.email
                    #         tail = 'Asisten Manager'
                    #         self.loa_request = 1
                    #     tujuan.append(teksmail)
                    #     template = 'salesorder_quotation_loa'
                    #     self.requestLoA = True
                    #     self.apvteks = tail
                    #     # self.state = 'requestloa'
                    #     self._sent_mail(tujuan, template, tail)
                    # else:
                        self.requestLoA = True
                        self.state = 'loaconfirmed'
                        idusr = self._uid
                        getusrs = self.env['res.users'].browse(idusr)
                        self.message_post(
                            body="Document Bypass LoA  By <b>" + getusrs.display_name + " <i>(" + getusrs.email + ")</i></b> because Jenis Project <b>" + str(
                                self.proj_type.name) + "</b> and Jenis Order <b>" + str(
                                self.ord_type.name) + "</b> , Document Ready to Confirm")
                # ---------------
        else:
            raise UserError('You dont have access to supervisor')

    def button_action_assman_rejected(self):
        if self.is_assman == True:
            self.state = 'spvcheck'
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Document Rejected Assman Check By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")
        else:
            raise UserError('You dont have access to Assistant Manager')
    
    def button_action_assman_approved(self):
        if self.is_assman == True:
            prosesLoa = True
            if self.jenis_so == 'Project':
                if self.proj_type.id != False and self.ord_type.id != False:
                    if self.proj_type.bypassLoA == True and self.ord_type.bypassLoA == True:
                        prosesLoa = False
                if prosesLoa and self.pek_type != False:
                    if self.pek_type.bypassLoA == True:
                        prosesLoa = False
            if prosesLoa == True:
                tujuan = []
                if self.required5 == True:
                    teksmail = self.penandatangan5.user_id.email
                    tail = 'Ketua Pengurus'
                    self.loa_request = 5
                if self.required4 == True:
                    teksmail = self.penandatangan4.user_id.email
                    tail = 'Pengurus/Direktur'
                    self.loa_request = 4
                if self.required3 == True:
                    teksmail = self.penandatangan3.user_id.email
                    tail = 'General Manager'
                    self.loa_request = 3
                if self.required2 == True:
                    teksmail = self.penandatangan2.user_id.email
                    tail = 'Manager'
                    self.loa_request = 2
                if self.required1 == True:
                    teksmail = self.penandatangan1.user_id.email
                    tail = 'Asisten Manager'
                    self.loa_request = 1
                tujuan.append(teksmail)
                template = 'salesorder_quotation_loa'
                self.requestLoA = True
                self.apvteks = tail
                self.state = 'requestloa'
                self._sent_mail(tujuan, template,tail)
            else:
                self.requestLoA = True
                self.state = 'loaconfirmed'
                idusr = self._uid
                getusrs = self.env['res.users'].browse(idusr)
                self.message_post(body="Document Bypass LoA  By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b> because Jenis Project <b>" + str(self.proj_type.name) + "</b> and Jenis Order <b>" + str(self.ord_type.name) + "</b> , Document Ready to Confirm")
        else:
            raise UserError('Access Denied, Only User Assman Sales can Request LoA Action')

    def button_action_bast_accepted(self):
        for doc in self:
            doc.allowInvoice = True
    
    @api.multi
    def _sent_mail(self, mailto = [], template = '', tail = ''):
        if len(mailto) > 0:
            penerima = ''
            ii = 0
            for terima in mailto:
                if ii == 0:
                    penerima = terima
                if ii > 0:
                    penerima = penerima + ';' + terima
                ii = ii + 1
            getmail = self.sudo().env['ir.mail_server'].search([('sequence','<=',10)])
            if len(getmail) > 0 and len(mailto) > 0:
                sendermail = getmail[0].smtp_user
                template_browse = self.sudo().env['mail.template'].search([('name','=',template)])
                if template_browse.id != False:
                    base_url = self.sudo().env['ir.config_parameter'].get_param('web.base.url')
                    base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
                    self.linktracker = base_url
                    kk = template_browse.generate_email(self.id,fields=None)
                    kk['email_to'] = penerima
                    kk['email_from'] = sendermail
                    kk['res_id'] = False
                    mail_obj = self.sudo().env['mail.mail']
                    msg_id = mail_obj.create(kk)
                    if tail != '':
                        msg_id.subject = msg_id.subject +' '+ str(tail)
                    msg_id.send()
        return True

    @api.multi
    def action_confirm(self):
        for doc in self:
            if len(doc.order_line) > 0:
                return super(SalesOrder, self).action_confirm()
            else:
                raise UserError('Order Line tidak boleh kosong')

    @api.multi
    def action_draft(self):
        self.requestLoA = False
        self.loa_request = False
        return super(SalesOrder,self).action_draft()

    @api.multi
    def press_approval(self):
        nextLoa = False
        idlanjut = 0
        tail = ''
        tujuan = []
        tailoroginal = self.apvteks
        if self.loa_request == 1:
            curent = self.penandatangan1
            if self.required2 == True:
                nextLoa = True
                idlanjut = 2
                tail = 'Manager'
                tujuan.append(self.penandatangan2.user_id.email)
        if self.loa_request == 2:
            curent = self.penandatangan2
            if self.required3 == True:
                nextLoa = True
                idlanjut = 3
                tail = 'General Manager'
                tujuan.append(self.penandatangan3.user_id.email)
        if self.loa_request == 3:
            curent = self.penandatangan3
            if self.required4 == True:
                nextLoa = True
                idlanjut = 4
                tail = 'Pengurus/Direktur'
                tujuan.append(self.penandatangan4.user_id.email)
        if self.loa_request == 4:
            curent = self.penandatangan4
            if self.required5 == True:
                nextLoa = True
                idlanjut = 5
                tail = 'Ketua Pengurus'
                tujuan.append(self.penandatangan5.user_id.email)
        if self.loa_request == 5:
            curent = self.penandatangan5

        if curent.user_id.id == self._uid:
            idusr = self._uid
            getusrs = self.env['res.users'].browse(idusr)
            self.message_post(body="Document LoA Level " + str(tailoroginal) + " Approved By <b>"+getusrs.display_name+" <i>("+getusrs.email+")</i></b>")
            if nextLoa == True:
                self.apvteks = tail
                self.loa_request = idlanjut
                template = 'salesorder_quotation_loa'
                self._sent_mail(tujuan, template,tail)
            else:
                tujuan.append(self.create_uid.email)
                self.apvteks = 'done'
                self.loa_request = 10
                self.state = 'loaconfirmed'
                template = 'salesorder_quotation_loa_done'
                self._sent_mail(tujuan, template,'')
        else:
            raise UserError('LoA Confirm, Access Denied')

    def button_action_baypass(self):
        self.state = 'loaconfirmed'

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'loaconfirmed').write({'state': 'sent'})
        return self.env.ref('sale.action_report_saleorder').report_action(self)
