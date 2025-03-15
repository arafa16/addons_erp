# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from odoo.tools import float_compare
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import *

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    # payment_ids = fields.One2many('account.payment.invoice', 'invoice_id', string='Invoices')
    journal_type = fields.Char(compute='_get_journal_type', store=True)
    bank_transfer_to_id = fields.Many2one('account.journal', string='Transfer To', domain=[('type', 'in', ('bank', 'cash'))])
    sign_by = fields.Many2one('hr.employee', string='Sign By')
    sale_nomor_spk = fields.Char(string='No. SPK / PO') #, readonly=True)
    purch_id_info = fields.Char(string="PO No.")
    created_sign_by = fields.Many2one('hr.employee', string='Dibuat', default=lambda self: self.env['res.config.settings'].get_values().get('default_created_sign_by'))
    checked_sign_by = fields.Many2one('hr.employee', string='Diperiksa', default=lambda self: self.env['res.config.settings'].get_values().get('default_checked_sign_by'))
    known_sign_by = fields.Many2one('hr.employee', string='Mengetahui', default=lambda self: self.env['res.config.settings'].get_values().get('default_known_sign_by'))
    done_sign_by = fields.Many2one('hr.employee', string='Dilaksanakan', default=lambda self: self.env['res.config.settings'].get_values().get('default_done_sign_by'))
    management_sign_by = fields.Many2one('hr.employee', string='Pengurus', default=lambda self: self.env['res.config.settings'].get_values().get('default_management_sign_by'))

    kpp_dpp_amount = fields.Monetary(string='DPP Amount')
    kpp_status = fields.Selection([('bersedia', 'Bersedia'), ('tidak bersedia', 'Tidak Bersedia')], 'Status')
    kpp_pph21 = fields.Selection([('Tarif 2,5%', 'Tarif 2,5%'), ('Tarif 5%', 'Tarif 5%')], 'PPh 21')
    kpp_pph21_op = fields.Char('Kode OP PPh 21')
    kpp_pph23 = fields.Selection([('Bunga/royalty/Hadiah**) sebesar 15%', 'Bunga/royalty/Hadiah**) sebesar 15%'), ('Jasa / Sewa*) sebesar 2%', 'Jasa / Sewa*) sebesar 2%')], 'PPh 23')
    kpp_pph23_op = fields.Char('Kode OP PPh 23')
    kpp_pph4_2 = fields.Selection([('None', 'None'), ('Ruang/Lahan/Listrik**) sebesar 10%', 'Ruang/Lahan/Listrik**) sebesar 10%')], 'PPh Pasal 4(2)')
    kpp_pph4_2_op_1 = fields.Char('Kode OP PPh Pasal 4(2)')
    kpp_pph4_2_1 = fields.Selection([('Klasifikasi menengah dan besar tarif 2,65%', 'Klasifikasi menengah dan besar tarif 2,65%'),
                                     ('Klasifikasi kecil tarif 1,75%', 'Klasifikasi kecil tarif 1,75%'),
                                     ('Tidak memiliki kualifikasi tarif 4%', 'Tidak memiliki kualifikasi tarif 4%')], 'PPh Pasal 4(2) Pelaksanaan')
    kpp_pph4_2_2 = fields.Selection([('Semua klasifikasi tarif 3,5%', 'Semua klasifikasi tarif 3,5%'),
                                     ('Tidak memiliki kualifikasi tarif 6%', 'Tidak memiliki kualifikasi tarif 6%')], 'PPh Pasal 4(2) Perencanaan')
    kpp_pph4_2_3 = fields.Selection([('Tidak memiliki SBU tarif 4%', 'Tidak memiliki SBU tarif 4%'),
                                     ('Memiliki SBU tarif 2,65%', 'Memiliki SBU tarif 2,65%')], 'PPh Pasal 4(2) Kontruksi')
    kpp_pph4_2_op_2 = fields.Char('Kode OP PPh Pasal 4(2)')
    fasilitas_pajak_1 = fields.Char('Nomor Bebas Pemotongan Pajak')
    fasilitas_pajak_2 = fields.Selection([('0,5% dipotong oleh Lintasarta', '0,5% dipotong oleh Lintasarta'),
                                          ('0,5% disetor sendiri (wajib melampirkan bukti penyetoran PPh)', '0,5% disetor sendiri (wajib melampirkan bukti penyetoran PPh)')], 'Kriteria Wajib Pajak')
    fasilitas_pajak_3 = fields.Char('Nomor Fasilitas Pajak lainnya')

    @api.onchange('kpp_status')
    def _onchange_kpp_status(self):
        if self.kpp_status == 'bersedia':
            self.kpp_dpp_amount = self.amount_untaxed
        else:
            self.kpp_dpp_amount = 0

    @api.multi
    def action_invoice_open(self):
        # to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        # if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == 0.0):
        #     raise UserError(_("You cannot validate an invoice with a zero total amount."))
        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def invoice_propose_payment_print(self):
        self.ensure_one()
        return self.env.ref('account_kopkarla.account_invoices_to_pay').report_action(self)

    def get_no_spk(self, origin):
        sale = self.env['sale.order'].sudo().search([('name', 'in', [origin]), ('nomor_spk', '!=', False)], limit=1)
        if sale:
            return sale.nomor_spk
        else:
            return '-'

    @api.model
    def create(self, vals):
        if 'bank_transfer_to_id' not in vals:
            default_bank_transfer_to_id = self.env['ir.config_parameter'].sudo().get_param('default_bank_transfer_to_id')
        else:
            default_bank_transfer_to_id = vals['bank_transfer_to_id']
        if 'sign_by' not in vals:
            default_sign_by_id = self.env['ir.config_parameter'].sudo().get_param('default_sign_by_id')
        else:
            default_sign_by_id = vals['sign_by']
        nomer_spk = False
        if 'origin' in vals:
            nomer_spk = self.get_no_spk(vals['origin'])
        vals.update({
            'sale_nomor_spk': nomer_spk,
            'bank_transfer_to_id': default_bank_transfer_to_id,
            'sign_by': default_sign_by_id,
        })
        return super(AccountInvoice, self).create(vals)

    @api.one
    @api.depends('journal_id')
    def _get_journal_type(self):
        self.journal_type = self.journal_id.type

    @api.multi
    def unlink(self):
        for invoice in self:
            if invoice.state not in ('draft', 'cancel'):
                raise UserError(('You cannot delete an invoice which is not draft or cancelled. You should create a credit note instead.'))
            elif invoice.move_name:
                if invoice.journal_id.sequence_id.implementation == 'no_gap':
                    raise UserError(('You cannot delete an invoice after it has been validated (and received a number) due to invoice number implementation is No gap.'))
                else:
                    invoice.move_name = None
        return super(AccountInvoice, self).unlink()

    @api.multi
    def register_payment_journal(self, payment_line, payment_journal, writeoff_acc_id=False, writeoff_journal_id=False):
        """ Reconcile payable/receivable lines from the invoice with payment_line """
        line_to_reconcile = self.env['account.move.line']
        for inv in self:
            line_to_reconcile += inv._get_aml_for_register_payment()
        return (line_to_reconcile + payment_line).reconcile_payment_journal(payment_journal) #, writeoff_acc_id, writeoff_journal_id)

    @api.model
    def tax_line_move_line_get(self):
        res = []
        # keep track of taxes already processed
        done_taxes = []
        # loop the invoice.tax.line in reversal sequence
        for tax_line in sorted(self.tax_line_ids, key=lambda x: -x.sequence):
            if tax_line.amount_total:
                tax = tax_line.tax_id
                if tax.amount_type == "group":
                    for child_tax in tax.children_tax_ids:
                        done_taxes.append(child_tax.id)
                res.append({
                    'invoice_tax_line_id': tax_line.id,
                    'tax_line_id': tax_line.tax_id.id,
                    'type': 'tax',
                    'name': tax_line.name,
                    'price_unit': tax_line.amount_total,
                    'quantity': 1,
                    'price': tax_line.amount_total,
                    'account_id': tax_line.account_id.id,
                    'account_analytic_id': tax_line.account_analytic_id.id,
                    'invoice_id': self.id,
                    'tax_ids': [(6, 0, list(done_taxes))] if tax_line.tax_id.include_base_amount else [],
                    'tax_no': self.FakturNumber,
                    'tax_date': self.FakturDate,
                })
                done_taxes.append(tax.id)
        return res

    # @api.model
    # def invoice_line_move_line_get(self):
    #     res = []
    #     for line in self.invoice_line_ids:
    #         if line.quantity==0:
    #             continue
    #         tax_ids = []
    #         for tax in line.invoice_line_tax_ids:
    #             tax_ids.append((4, tax.id, None))
    #             for child in tax.children_tax_ids:
    #                 if child.type_tax_use != 'none':
    #                     tax_ids.append((4, child.id, None))
    #         analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]
    #
    #         move_line_dict = {
    #             'invl_id': line.id,
    #             'type': 'src',
    #             'name': line.name.split('\n')[0][:64],
    #             'price_unit': line.price_unit,
    #             'quantity': line.quantity,
    #             'price': line.price_subtotal,
    #             'account_id': line.account_id.id,
    #             'product_id': line.product_id.id,
    #             'uom_id': line.uom_id.id,
    #             'account_analytic_id': line.account_analytic_id.id,
    #             'tax_ids': tax_ids,
    #             'invoice_id': self.id,
    #             'analytic_tag_ids': analytic_tag_ids
    #         }
    #         if 'cost_center_id' in line._fields:
    #             move_line_dict['cost_center_id'] = line.cost_center_id.id
    #         res.append(move_line_dict)
    #     return res
