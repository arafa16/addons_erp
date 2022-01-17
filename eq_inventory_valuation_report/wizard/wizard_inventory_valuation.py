# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2019 EquickERP
#
##############################################################################

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from datetime import datetime, date
from odoo.tools.misc import formatLang


class wizard_inventory_valuation(models.TransientModel):
    _name = 'wizard.inventory.valuation'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    warehouse_ids = fields.Many2many('stock.warehouse', string='Warehouse')
    location_ids = fields.Many2many('stock.location', string='Location')
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    filter_by = fields.Selection([('product', 'Product'), ('category', 'Category')], string="Filter By")
    group_by_categ = fields.Boolean(string="Group By Category")
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    name = fields.Char(string='File Name', readonly=True)
    data = fields.Binary(string='File', readonly=True)
    product_ids = fields.Many2many('product.product', string="Products")
    category_ids = fields.Many2many('product.category', string="Categories")

    @api.onchange('company_id')
    def onchange_company_id(self):
        domain = [('id', 'in', self.env.user.company_ids.ids)]
        if self.company_id:
            self.warehouse_ids = False
            self.location_ids = False
        return {'domain':{'company_id':domain}}

    @api.onchange('warehouse_ids')
    def onchange_warehouse_ids(self):
        stock_location_obj = self.env['stock.location']
        location_ids = stock_location_obj.search([('usage', '=', 'internal'), ('company_id', '=', self.company_id.id)])
        addtional_ids = []
        if self.warehouse_ids:
            for warehouse in self.warehouse_ids:
                addtional_ids.extend([y.id for y in stock_location_obj.search([('location_id', 'child_of', warehouse.view_location_id.id), ('usage', '=', 'internal')])])
            self.location_ids = False
        return {'domain':{'location_ids':[('id', 'in', addtional_ids)]}}

    def check_date_range(self):
        if self.end_date < self.start_date:
            raise ValidationError(_('End Date should be greater than Start Date.'))

    @api.onchange('filter_by')
    def onchange_filter_by(self):
        self.product_ids = False
        self.category_ids = False

    @api.multi
    def print_report(self):
        self.check_date_range()
        datas = {'form':
                    {
                        'company_id': self.company_id.id,
                        'warehouse_ids': [y.id for y in self.warehouse_ids],
                        'location_ids': self.location_ids.ids or False,
                        'start_date': self.start_date,
                        'end_date': self.end_date,
                        'id': self.id,
                        'product_ids': self.product_ids.ids,
                        'product_categ_ids': self.category_ids.ids
                    },
                }
        return self.env.ref('eq_inventory_valuation_report.action_inventory_valuation_template').report_action(self, data=datas)

    @api.multi
    def go_back(self):
        self.state = 'choose'
        return {
            'name': 'Inventory Valuation Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.multi
    def print_xls_report(self):
        self.check_date_range()
        xls_filename = 'inventory valuation report.xlsx'
        workbook = xlsxwriter.Workbook('/tmp/' + xls_filename)
        report_stock_inv_obj = self.env['report.eq_inventory_valuation_report.inventory_valuation_report']

        header_merge_format = workbook.add_format({'bold':True, 'align':'center', 'valign':'vcenter', \
                                            'font_size':10, 'bg_color':'#D3D3D3', 'border':1})

        header_data_format = workbook.add_format({'align':'center', 'valign':'vcenter', \
                                                   'font_size':10, 'border':1})

        product_header_format = workbook.add_format({'valign':'vcenter', 'font_size':10, 'border':1})

        for warehouse in self.warehouse_ids:
            worksheet = workbook.add_worksheet(warehouse.name)
            worksheet.merge_range(0, 0, 2, 8, "Inventory Valuation Report", header_merge_format)

            worksheet.set_column('A:B', 15)
            worksheet.set_column('C:C', 13)
            worksheet.write(5, 0, 'Company', header_merge_format)
            worksheet.write(5, 1, 'Warehouse', header_merge_format)
            worksheet.write(5, 2, 'Start Date', header_merge_format)
            worksheet.write(5, 3, 'End Date', header_merge_format)

            worksheet.write(6, 0, self.company_id.name, header_data_format)
            worksheet.write(6, 1, warehouse.name, header_data_format)
            worksheet.write(6, 2, self.start_date, header_data_format)
            worksheet.write(6, 3, self.end_date, header_data_format)

            if not self.location_ids:
                worksheet.set_column('D:H', 9)
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                worksheet.write(9, 2, "Costing Method", header_merge_format)
                worksheet.merge_range(9,3,9,4, "Beginning", header_merge_format)
                worksheet.merge_range(9,5,9,6, "Received", header_merge_format)
                worksheet.merge_range(9,7,9,8, "Sales", header_merge_format)
                worksheet.merge_range(9,9,9,10, "Internal", header_merge_format)
                worksheet.merge_range(9,11,9,12, "Adjustments", header_merge_format)
                worksheet.merge_range(9,13,9,15, "Ending", header_merge_format)
                worksheet.write(10,3, "Qty", header_merge_format)
                worksheet.write(10,4, "Value", header_merge_format)
                worksheet.write(10,5, "Qty", header_merge_format)
                worksheet.write(10,6, "Value", header_merge_format)
                worksheet.write(10,7, "Qty", header_merge_format)
                worksheet.write(10,8, "Value", header_merge_format)
                worksheet.write(10,9, "Qty", header_merge_format)
                worksheet.write(10,10, "Value", header_merge_format)
                worksheet.write(10,11, "Qty", header_merge_format)
                worksheet.write(10,12, "Value", header_merge_format)
                worksheet.write(10,13, "Qty", header_merge_format)
                worksheet.write(10,14, "Unit Price", header_merge_format)
                worksheet.write(10,15, "Value", header_merge_format)

                rows = 11
                prod_beginning_qty = prod_qty_in = prod_qty_out = prod_qty_int = prod_qty_adjust = prod_ending_qty = 0.00
                prod_beginning_qty_val = prod_qty_in_val = prod_qty_out_val = prod_qty_int_val = prod_qty_adjust_val = prod_ending_qty_val = 0.00
                if not self.group_by_categ:
                    for product in report_stock_inv_obj._get_products(self):
                        beginning_qty = report_stock_inv_obj._get_beginning_inventory(self, product, warehouse)
                        beginning_qty_val = report_stock_inv_obj.get_product_valuation(self,product,beginning_qty,warehouse)
                        product_val = report_stock_inv_obj.get_product_sale_qty(self, warehouse, product)
                        product_qty_in = product_val.get('product_qty_in')
                        product_qty_in_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_in,warehouse)
                        product_qty_out = product_val.get('product_qty_out')
                        product_qty_out_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_out,warehouse)
                        product_qty_internal = product_val.get('product_qty_internal')
                        product_qty_internal_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_internal,warehouse)
                        product_qty_adjustment = product_val.get('product_qty_adjustment')
                        product_qty_adjustment_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_adjustment,warehouse)

                        ending_qty = beginning_qty + product_qty_in + product_qty_out\
                                    + product_qty_internal + product_qty_adjustment
                        ending_qty_val = report_stock_inv_obj.get_product_valuation(self,product,ending_qty,warehouse)

                        worksheet.merge_range(rows, 0, rows, 1, product.display_name, product_header_format)
                        cost_method =  dict(product.categ_id.fields_get()['property_cost_method']['selection'])[product.categ_id.property_cost_method]
                        worksheet.write(rows, 2, cost_method, header_data_format)
                        worksheet.write(rows, 3, beginning_qty, header_data_format)
                        worksheet.write(rows, 4, formatLang(self.env, beginning_qty_val), header_data_format)
                        worksheet.write(rows, 5, product_qty_in, header_data_format)
                        worksheet.write(rows, 6, formatLang(self.env, product_qty_in_val), header_data_format)
                        worksheet.write(rows, 7, abs(product_qty_out), header_data_format)
                        worksheet.write(rows, 8, formatLang(self.env, abs(product_qty_out_val)), header_data_format)
                        worksheet.write(rows, 9, product_qty_internal, header_data_format)
                        worksheet.write(rows, 10, formatLang(self.env, product_qty_internal_val), header_data_format)
                        worksheet.write(rows, 11, product_qty_adjustment, header_data_format)
                        worksheet.write(rows, 12, formatLang(self.env, product_qty_adjustment_val), header_data_format)
                        worksheet.write(rows, 13, ending_qty, header_data_format)
                        worksheet.write(rows, 14, ending_qty and formatLang(self.env, ending_qty_val / ending_qty) or 0, header_data_format)
                        worksheet.write(rows, 15, formatLang(self.env, ending_qty_val), header_data_format)

                        prod_beginning_qty += beginning_qty
                        prod_beginning_qty_val += beginning_qty_val
                        prod_qty_in += product_qty_in
                        prod_qty_in_val += product_qty_in_val
                        prod_qty_out += product_qty_out
                        prod_qty_out_val += product_qty_out_val
                        prod_qty_int += product_qty_internal
                        prod_qty_int_val += product_qty_internal_val
                        prod_qty_adjust += product_qty_adjustment
                        prod_qty_adjust_val += product_qty_adjustment_val
                        prod_ending_qty += ending_qty
                        prod_ending_qty_val += ending_qty_val
                        rows += 1

                    worksheet.merge_range(rows + 1, 0, rows + 1, 2, 'Total', header_merge_format)
                    worksheet.write(rows + 1, 3, prod_beginning_qty, header_merge_format)
                    worksheet.write(rows + 1, 4, formatLang(self.env, prod_beginning_qty_val), header_merge_format)
                    worksheet.write(rows + 1, 5, prod_qty_in, header_merge_format)
                    worksheet.write(rows + 1, 6, formatLang(self.env, prod_qty_in_val), header_merge_format)
                    worksheet.write(rows + 1, 7, abs(prod_qty_out), header_merge_format)
                    worksheet.write(rows + 1, 8, formatLang(self.env, abs(prod_qty_out_val)), header_merge_format)
                    worksheet.write(rows + 1, 9, prod_qty_int, header_merge_format)
                    worksheet.write(rows + 1, 10, formatLang(self.env, prod_qty_int_val), header_merge_format)
                    worksheet.write(rows + 1, 11, prod_qty_adjust, header_merge_format)
                    worksheet.write(rows + 1, 12, formatLang(self.env, prod_qty_adjust_val), header_merge_format)
                    worksheet.write(rows + 1, 13, prod_ending_qty, header_merge_format)
                    worksheet.write(rows + 1, 14, prod_ending_qty and formatLang(self.env, prod_ending_qty_val / prod_ending_qty) or 0, header_merge_format)
                    worksheet.write(rows + 1, 15, formatLang(self.env, prod_ending_qty_val), header_merge_format)

                else:
                    rows += 1
                    product_val = report_stock_inv_obj.get_product_sale_qty(self, warehouse)
                    for categ, product_value in product_val.items():
                        categ_prod_beginning_qty = categ_prod_qty_in = categ_prod_qty_out = categ_prod_qty_int = categ_prod_qty_adjust = categ_prod_ending_qty = 0.00
                        categ_prod_beginning_qty_val = categ_prod_qty_in_val = categ_prod_qty_out_val = categ_prod_qty_int_val = categ_prod_qty_adjust_val = categ_prod_ending_qty_val = 0.00
                        worksheet.merge_range(rows, 0, rows, 15, self.env['product.category'].browse(categ).name, header_merge_format)
                        rows += 1
                        for product in product_value:
                            product_id = self.env['product.product'].browse(product['product_id'])
                            beginning_qty = report_stock_inv_obj._get_beginning_inventory(self, product_id.id, warehouse)
                            beginning_qty_val = report_stock_inv_obj.get_product_valuation(self,product_id,beginning_qty,warehouse)
                            product_qty_in = product.get('product_qty_in')
                            product_qty_in_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_in,warehouse)
                            product_qty_out = product.get('product_qty_out')
                            product_qty_out_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_out,warehouse)
                            product_qty_internal = product.get('product_qty_internal')
                            product_qty_internal_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_internal,warehouse)
                            product_qty_adjustment = product.get('product_qty_adjustment')
                            product_qty_adjustment_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_adjustment,warehouse)
                            ending_qty = beginning_qty + product_qty_in + product_qty_out + product_qty_internal + product_qty_adjustment
                            ending_qty_val = report_stock_inv_obj.get_product_valuation(self,product_id,ending_qty,warehouse)

                            worksheet.merge_range(rows, 0 , rows, 1, product_id.display_name, product_header_format)
                            cost_method =  dict(product_id.categ_id.fields_get()['property_cost_method']['selection'])[product_id.categ_id.property_cost_method]
                            worksheet.write(rows, 2, cost_method, header_data_format)

                            worksheet.write(rows, 3, beginning_qty, header_data_format)
                            worksheet.write(rows, 4, formatLang(self.env, beginning_qty_val), header_data_format)
                            worksheet.write(rows, 5, product_qty_in, header_data_format)
                            worksheet.write(rows, 6, formatLang(self.env, product_qty_in_val), header_data_format)
                            worksheet.write(rows, 7, abs(product_qty_out), header_data_format)
                            worksheet.write(rows, 8, formatLang(self.env, abs(product_qty_out_val)), header_data_format)
                            worksheet.write(rows, 9, product_qty_internal, header_data_format)
                            worksheet.write(rows, 10, formatLang(self.env, product_qty_internal_val), header_data_format)
                            worksheet.write(rows, 11, product_qty_adjustment, header_data_format)
                            worksheet.write(rows, 12, formatLang(self.env, product_qty_adjustment_val), header_data_format)
                            worksheet.write(rows, 13, ending_qty, header_data_format)
                            worksheet.write(rows, 14, ending_qty and formatLang(self.env, ending_qty_val / ending_qty) or 0, header_data_format)
                            worksheet.write(rows, 15, formatLang(self.env, ending_qty_val), header_data_format)

                            categ_prod_beginning_qty += beginning_qty
                            categ_prod_qty_in += product_qty_in
                            categ_prod_qty_out += product_qty_out
                            categ_prod_qty_int += product_qty_internal
                            categ_prod_qty_adjust += product_qty_adjustment
                            categ_prod_ending_qty += ending_qty

                            categ_prod_beginning_qty_val += beginning_qty_val
                            categ_prod_qty_in_val += product_qty_in_val
                            categ_prod_qty_out_val += product_qty_out_val
                            categ_prod_qty_int_val += product_qty_internal_val
                            categ_prod_qty_adjust_val += product_qty_adjustment_val
                            categ_prod_ending_qty_val += ending_qty_val
                            rows += 1

                        worksheet.merge_range(rows, 0 , rows, 2, 'Total', header_merge_format)
                        worksheet.write(rows, 3, categ_prod_beginning_qty, header_merge_format)
                        worksheet.write(rows, 4, formatLang(self.env, categ_prod_beginning_qty_val), header_merge_format)
                        worksheet.write(rows, 5, categ_prod_qty_in, header_merge_format)
                        worksheet.write(rows, 6, formatLang(self.env, categ_prod_qty_in_val), header_merge_format)
                        worksheet.write(rows, 7, abs(categ_prod_qty_out), header_merge_format)
                        worksheet.write(rows, 8, formatLang(self.env, abs(categ_prod_qty_out_val)), header_merge_format)
                        worksheet.write(rows, 9, categ_prod_qty_int, header_merge_format)
                        worksheet.write(rows, 10, formatLang(self.env, categ_prod_qty_int_val), header_merge_format)
                        worksheet.write(rows, 11, categ_prod_qty_adjust, header_merge_format)
                        worksheet.write(rows, 12, formatLang(self.env, categ_prod_qty_adjust_val), header_merge_format)
                        worksheet.write(rows, 13, categ_prod_ending_qty, header_merge_format)
                        worksheet.write(rows, 14, categ_prod_ending_qty and formatLang(self.env, categ_prod_ending_qty_val / categ_prod_ending_qty) or 0, header_merge_format)
                        worksheet.write(rows, 15, formatLang(self.env, categ_prod_ending_qty_val), header_merge_format)

                        prod_qty_in += categ_prod_qty_in
                        prod_qty_out += categ_prod_qty_out
                        prod_qty_int += categ_prod_qty_int
                        prod_qty_adjust += categ_prod_qty_adjust
                        prod_ending_qty += categ_prod_ending_qty
                        prod_beginning_qty += categ_prod_beginning_qty

                        prod_beginning_qty_val += categ_prod_beginning_qty_val
                        prod_qty_in_val += categ_prod_qty_in_val
                        prod_qty_out_val += categ_prod_qty_out_val
                        prod_qty_int_val += categ_prod_qty_int_val
                        prod_qty_adjust_val += categ_prod_qty_adjust_val
                        prod_ending_qty_val += categ_prod_ending_qty_val
                        rows += 2

            else:
                worksheet.set_column('D:D', 13)
                worksheet.set_column('E:H', 9)
                worksheet.merge_range(9, 0, 9, 1, "Products", header_merge_format)
                worksheet.write(9, 2, "Costing Method", header_merge_format)
                worksheet.write(9, 3, "Location", header_merge_format)
                worksheet.merge_range(9,4,9,5, "Beginning", header_merge_format)
                worksheet.merge_range(9,6,9,7, "Received", header_merge_format)
                worksheet.merge_range(9,8,9,9, "Sales", header_merge_format)
                worksheet.merge_range(9,10,9,11, "Internal", header_merge_format)
                worksheet.merge_range(9,12,9,13, "Adjustments", header_merge_format)
                worksheet.merge_range(9,14,9,16, "Ending", header_merge_format)
                worksheet.write(10,4, "Qty", header_merge_format)
                worksheet.write(10,5, "Value", header_merge_format)
                worksheet.write(10,6, "Qty", header_merge_format)
                worksheet.write(10,7, "Value", header_merge_format)
                worksheet.write(10,8, "Qty", header_merge_format)
                worksheet.write(10,9, "Value", header_merge_format)
                worksheet.write(10,10, "Qty", header_merge_format)
                worksheet.write(10,11, "Value", header_merge_format)
                worksheet.write(10,12, "Qty", header_merge_format)
                worksheet.write(10,13, "Value", header_merge_format)
                worksheet.write(10,14, "Qty", header_merge_format)
                worksheet.write(10,15, "Unit Price", header_merge_format)
                worksheet.write(10,16, "Value", header_merge_format)

                rows = 11
                prod_beginning_qty = prod_qty_in = prod_qty_out = prod_qty_int = prod_qty_adjust = prod_ending_qty = 0.00
                prod_beginning_qty_val = prod_qty_in_val = prod_qty_out_val = prod_qty_int_val = prod_qty_adjust_val = prod_ending_qty_val = 0.00
                location_ids = report_stock_inv_obj.get_warehouse_wise_location(self, warehouse)
                if not self.group_by_categ:
                    for product in report_stock_inv_obj._get_products(self):
                        location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product, location_ids)
                        beginning_qty = location_wise_data[1][0]
                        beginning_qty_val = report_stock_inv_obj.get_product_valuation(self,product,beginning_qty,warehouse)
                        product_qty_in = location_wise_data[1][1]
                        product_qty_in_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_in,warehouse)
                        product_qty_out = location_wise_data[1][2]
                        product_qty_out_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_out,warehouse)
                        product_qty_internal = location_wise_data[1][3]
                        product_qty_internal_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_internal,warehouse)
                        product_qty_adjustment = location_wise_data[1][4]
                        product_qty_adjustment_val = report_stock_inv_obj.get_product_valuation(self,product,product_qty_adjustment,warehouse)
                        ending_qty = location_wise_data[1][5]
                        ending_qty_val = report_stock_inv_obj.get_product_valuation(self,product,ending_qty,warehouse)

                        worksheet.merge_range(rows, 0, rows, 1, product.display_name, product_header_format)
                        cost_method =  dict(product.categ_id.fields_get()['property_cost_method']['selection'])[product.categ_id.property_cost_method]
                        worksheet.write(rows, 2, cost_method, header_data_format)
                        worksheet.write(rows, 3, ' ', header_data_format)
                        worksheet.write(rows, 4, beginning_qty, header_merge_format)
                        worksheet.write(rows, 5, formatLang(self.env, beginning_qty_val), header_merge_format)
                        worksheet.write(rows, 6, product_qty_in, header_merge_format)
                        worksheet.write(rows, 7, formatLang(self.env, product_qty_in_val), header_merge_format)
                        worksheet.write(rows, 8, abs(product_qty_out), header_merge_format)
                        worksheet.write(rows, 9, formatLang(self.env, abs(product_qty_out_val)), header_merge_format)
                        worksheet.write(rows, 10, product_qty_internal, header_merge_format)
                        worksheet.write(rows, 11, formatLang(self.env, product_qty_internal_val), header_merge_format)
                        worksheet.write(rows, 12, product_qty_adjustment, header_merge_format)
                        worksheet.write(rows, 13, formatLang(self.env, product_qty_adjustment_val), header_merge_format)
                        worksheet.write(rows, 14, ending_qty, header_merge_format)
                        worksheet.write(rows, 15, ending_qty and formatLang(self.env, ending_qty_val / ending_qty) or 0, header_merge_format)
                        worksheet.write(rows, 16, formatLang(self.env, ending_qty_val), header_merge_format)
                        rows += 1

                        for location, value in location_wise_data[0].items():
                            worksheet.merge_range(rows, 0, rows, 2, '', header_data_format)
                            worksheet.write(rows, 3, location.display_name, header_data_format)
                            worksheet.write(rows, 4, value[0], header_data_format)
                            worksheet.write(rows, 5, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product,value[0],warehouse)), header_data_format)
                            worksheet.write(rows, 6, value[1], header_data_format)
                            worksheet.write(rows, 7, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product,value[1],warehouse)), header_data_format)
                            worksheet.write(rows, 8, abs(value[2]), header_data_format)
                            worksheet.write(rows, 9, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product,abs(value[2]),warehouse)), header_data_format)
                            worksheet.write(rows, 10, value[3], header_data_format)
                            worksheet.write(rows, 11, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product,value[3],warehouse)), header_data_format)
                            worksheet.write(rows, 12, value[4], header_data_format)
                            worksheet.write(rows, 13, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product,value[4],warehouse)), header_data_format)
                            worksheet.write(rows, 14, value[5], header_data_format)
                            worksheet.write(rows, 15, value[5] and formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product,value[5],warehouse) / value[5]) or 0, header_data_format)
                            worksheet.write(rows, 16, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product,value[5],warehouse)), header_data_format)
                            rows += 1

                        prod_beginning_qty += beginning_qty
                        prod_beginning_qty_val += beginning_qty_val
                        prod_qty_in += product_qty_in
                        prod_qty_in_val += product_qty_in_val
                        prod_qty_out += product_qty_out
                        prod_qty_out_val += product_qty_out_val
                        prod_qty_int += product_qty_internal
                        prod_qty_int_val += product_qty_internal_val
                        prod_qty_adjust += product_qty_adjustment
                        prod_qty_adjust_val += product_qty_adjustment_val
                        prod_ending_qty += ending_qty
                        prod_ending_qty_val += ending_qty_val

                    rows += 1
                    worksheet.merge_range(rows, 0, rows, 3, 'Total', header_merge_format)
                    worksheet.write(rows, 4, prod_beginning_qty, header_merge_format)
                    worksheet.write(rows, 5, formatLang(self.env, prod_beginning_qty_val), header_merge_format)
                    worksheet.write(rows, 6, prod_qty_in, header_merge_format)
                    worksheet.write(rows, 7, formatLang(self.env, prod_qty_in_val), header_merge_format)
                    worksheet.write(rows, 8, abs(prod_qty_out), header_merge_format)
                    worksheet.write(rows, 9, formatLang(self.env, abs(prod_qty_out_val)), header_merge_format)
                    worksheet.write(rows, 10, prod_qty_int, header_merge_format)
                    worksheet.write(rows, 11, formatLang(self.env, prod_qty_int_val), header_merge_format)
                    worksheet.write(rows, 12, prod_qty_adjust, header_merge_format)
                    worksheet.write(rows, 13, formatLang(self.env, prod_qty_adjust_val), header_merge_format)
                    worksheet.write(rows, 14, prod_ending_qty, header_merge_format)
                    worksheet.write(rows, 15, prod_ending_qty and formatLang(self.env, prod_ending_qty_val / prod_ending_qty) or 0, header_merge_format)
                    worksheet.write(rows, 16, formatLang(self.env, prod_ending_qty_val), header_merge_format)

                else:
                    rows+=1
                    product_val = report_stock_inv_obj.get_product_sale_qty(self, warehouse)
                    for categ, product_value in product_val.items():
                        categ_prod_beginning_qty = categ_prod_qty_in = categ_prod_qty_out = categ_prod_qty_int = categ_prod_qty_adjust = categ_prod_ending_qty = 0.00
                        categ_prod_beginning_qty_val = categ_prod_qty_in_val = categ_prod_qty_out_val = categ_prod_qty_int_val = categ_prod_qty_adjust_val = categ_prod_ending_qty_val = 0.00
                        worksheet.merge_range(rows, 0, rows, 15, self.env['product.category'].browse(categ).name, header_merge_format)
                        rows += 1
                        for product in product_value:
                            product_id = self.env['product.product'].browse(product['product_id'])
                            location_wise_data = report_stock_inv_obj.get_location_wise_product(self, warehouse, product_id, location_ids)
                            beginning_qty = location_wise_data[1][0]
                            beginning_qty_val = report_stock_inv_obj.get_product_valuation(self,product_id,beginning_qty,warehouse)
                            product_qty_in = location_wise_data[1][1]
                            product_qty_in_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_in,warehouse)
                            product_qty_out = abs(location_wise_data[1][2])
                            product_qty_out_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_out,warehouse)
                            product_qty_internal = location_wise_data[1][3]
                            product_qty_internal_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_internal,warehouse)
                            product_qty_adjustment = location_wise_data[1][4]
                            product_qty_adjustment_val = report_stock_inv_obj.get_product_valuation(self,product_id,product_qty_adjustment,warehouse)
                            ending_qty = location_wise_data[1][5]
                            ending_qty_val = report_stock_inv_obj.get_product_valuation(self,product_id,ending_qty,warehouse)

                            worksheet.merge_range(rows, 0, rows, 1, product_id.display_name, product_header_format)
                            cost_method =  dict(product_id.categ_id.fields_get()['property_cost_method']['selection'])[product_id.categ_id.property_cost_method]
                            worksheet.write(rows, 2, cost_method, header_data_format)
                            worksheet.write(rows, 3, ' ', header_data_format)
                            worksheet.write(rows, 4, beginning_qty, header_merge_format)
                            worksheet.write(rows, 5, formatLang(self.env, beginning_qty_val), header_merge_format)
                            worksheet.write(rows, 6, product_qty_in, header_merge_format)
                            worksheet.write(rows, 7, formatLang(self.env, product_qty_in_val), header_merge_format)
                            worksheet.write(rows, 8, abs(product_qty_out), header_merge_format)
                            worksheet.write(rows, 9, formatLang(self.env, abs(product_qty_out_val)), header_merge_format)
                            worksheet.write(rows, 10, product_qty_internal, header_merge_format)
                            worksheet.write(rows, 11, formatLang(self.env, product_qty_internal_val), header_merge_format)
                            worksheet.write(rows, 12, product_qty_adjustment, header_merge_format)
                            worksheet.write(rows, 13, formatLang(self.env, product_qty_adjustment_val), header_merge_format)
                            worksheet.write(rows, 14, ending_qty, header_merge_format)
                            worksheet.write(rows, 15, ending_qty and formatLang(self.env, ending_qty_val / ending_qty) or 0, header_merge_format)
                            worksheet.write(rows, 16, formatLang(self.env, ending_qty_val), header_merge_format)
                            rows += 1

                            for location, value in location_wise_data[0].items():
                                worksheet.merge_range(rows, 0, rows, 2, '', header_data_format)
                                worksheet.write(rows, 3, location.display_name, header_data_format)
                                worksheet.write(rows, 4, value[0], header_data_format)
                                worksheet.write(rows, 5, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product_id,value[0],warehouse)), header_data_format)
                                worksheet.write(rows, 6, value[1], header_data_format)
                                worksheet.write(rows, 7, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product_id,value[1],warehouse)), header_data_format)
                                worksheet.write(rows, 8, abs(value[2]), header_data_format)
                                worksheet.write(rows, 9, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product_id,abs(value[2]),warehouse)), header_data_format)
                                worksheet.write(rows, 10, value[3], header_data_format)
                                worksheet.write(rows, 11, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product_id,value[3],warehouse)), header_data_format)
                                worksheet.write(rows, 12, value[4], header_data_format)
                                worksheet.write(rows, 13, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product_id,value[4],warehouse)), header_data_format)
                                worksheet.write(rows, 14, value[5], header_data_format)
                                worksheet.write(rows, 15, value[5] and formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product_id,value[5],warehouse) / value[5]) or 0, header_data_format)
                                worksheet.write(rows, 16, formatLang(self.env, report_stock_inv_obj.get_product_valuation(self,product_id,value[5],warehouse)), header_data_format)
                                rows += 1

                            categ_prod_beginning_qty += beginning_qty
                            categ_prod_qty_in += product_qty_in
                            categ_prod_qty_out += product_qty_out
                            categ_prod_qty_int += product_qty_internal
                            categ_prod_qty_adjust += product_qty_adjustment
                            categ_prod_ending_qty += ending_qty

                            categ_prod_beginning_qty_val += beginning_qty_val
                            categ_prod_qty_in_val += product_qty_in_val
                            categ_prod_qty_out_val += product_qty_out_val
                            categ_prod_qty_int_val += product_qty_internal_val
                            categ_prod_qty_adjust_val += product_qty_adjustment_val
                            categ_prod_ending_qty_val += ending_qty_val

                        worksheet.merge_range(rows, 0, rows, 3, 'Total', header_merge_format)
                        worksheet.write(rows, 4, categ_prod_beginning_qty, header_merge_format)
                        worksheet.write(rows, 5, formatLang(self.env, categ_prod_beginning_qty_val), header_merge_format)
                        worksheet.write(rows, 6, categ_prod_qty_in, header_merge_format)
                        worksheet.write(rows, 7, formatLang(self.env, categ_prod_qty_in_val), header_merge_format)
                        worksheet.write(rows, 8, abs(categ_prod_qty_out), header_merge_format)
                        worksheet.write(rows, 9, formatLang(self.env, abs(categ_prod_qty_out_val)), header_merge_format)
                        worksheet.write(rows, 10, categ_prod_qty_int, header_merge_format)
                        worksheet.write(rows, 11, formatLang(self.env, categ_prod_qty_int_val), header_merge_format)
                        worksheet.write(rows, 12, categ_prod_qty_adjust, header_merge_format)
                        worksheet.write(rows, 13, formatLang(self.env, categ_prod_qty_adjust_val), header_merge_format)
                        worksheet.write(rows, 14, categ_prod_ending_qty, header_merge_format)
                        worksheet.write(rows, 15, categ_prod_ending_qty and formatLang(self.env, categ_prod_ending_qty_val / categ_prod_ending_qty) or 0, header_merge_format)
                        worksheet.write(rows, 16, formatLang(self.env, categ_prod_ending_qty_val), header_merge_format)
                        rows += 1
                        rows += 2

        workbook.close()
        self.write({
            'state': 'get',
            'data': base64.b64encode(open('/tmp/' + xls_filename, 'rb').read()),
            'name': xls_filename
        })
        return {
            'name': 'Inventory Valuation Report',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: