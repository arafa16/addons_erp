from odoo import api, fields, models, _


class PurchaseRequestType(models.Model):
    _name = 'purchase.request.type'
    _rec_name = 'prod_categ_id'
    _description = 'PR Type'

    prod_categ_id = fields.Many2one('product.category', 'Product Category')
    account_trade_request_id = fields.Many2one('account.account', 'Trading Elektronik')
    account_trd_brt_request_id = fields.Many2one('account.account', 'Trading BRT')
    account_trd_perl_kantor_request_id = fields.Many2one('account.account', 'Trading Perlengkapan Kantor')
    account_trd_voucher_pulsa_request_id = fields.Many2one('account.account', 'Trading Voucher Pulsa')
    account_trd_sarpen_request_id = fields.Many2one('account.account', 'Trading Sarpen')
    account_trd_ecommerce_id = fields.Many2one('account.account', 'Trading E-Commerce')

    account_datacom_request_id = fields.Many2one('account.account', 'Datacom PSB')
    account_dtc_fo_lastmile_request_id = fields.Many2one('account.account', 'Datacom FO Lastmile')
    account_dtc_pmcm_fo_request_id = fields.Many2one('account.account', 'Datacom PMCM FO')
    account_dtc_pmcm_central_request_id = fields.Many2one('account.account', 'Datacom PMCM Central')
    account_dtc_pmtl_remote_request_id = fields.Many2one('account.account', 'Datacom PMTL Remote')
    account_dtc_dtc_project_request_id = fields.Many2one('account.account', 'Datacom Project')
    account_dtc_dtc_tools_request_id = fields.Many2one('account.account', 'Datacom Tools')
    account_dtc_dtc_sewa_home_base_request_id = fields.Many2one('account.account', 'Datacom Sewa Home Base')
    account_dtc_dtc_brt_request_id = fields.Many2one('account.account', 'Datacom BRT')

    account_overhead_request_id = fields.Many2one('account.account', 'Overhead Account')
