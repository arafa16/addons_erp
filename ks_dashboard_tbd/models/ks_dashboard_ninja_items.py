from odoo import models, fields, api, _


class KsDashboardNinjaItems(models.Model):
    _inherit = 'ks_dashboard_ninja.item'

    show_full_amount = fields.Boolean(string="Show Full Amount")
    # use_system_unit = fields.Boolean(string="Use System Unit")
    legend_bar_position = fields.Selection([('top', 'Top'),('bottom', 'Bottom')], string="Legend Position", default='top')
    ks_record_count_type = fields.Selection(selection_add=[('count_distinct', 'Count Distinct')])
    ks_record_field3 = fields.Many2one('ir.model.fields',
                                      domain="[('model_id','=',ks_model_id),('name','!=','id'),('store','=',True)]",
                                      string="Record Field")

    @api.multi
    @api.depends('ks_record_count_type', 'ks_model_id', 'ks_domain', 'ks_record_field', 'ks_date_filter_field',
                 'ks_item_end_date', 'ks_item_start_date', 'ks_compare_period', 'ks_year_period',
                 'ks_dashboard_item_type', 'ks_domain_extension', 'ks_record_data_limit', 'ks_record_field3')
    def ks_get_record_count(self):
        for rec in self:
            if rec.ks_record_count_type == 'count' or rec.ks_dashboard_item_type == 'ks_list_view':
                rec.ks_record_count = rec.ks_fetch_model_data(rec.ks_model_name, rec.ks_domain, 'search_count', rec)
            elif rec.ks_record_count_type == 'count_distinct' and rec.ks_record_field3 and rec.ks_dashboard_item_type == 'ks_tile':
                proper_domain = rec.ks_convert_into_proper_domain(rec.ks_domain, rec)
                ks_records_grouped_data = self.env[rec.ks_model_name].read_group(proper_domain, [rec.ks_record_field3.name], [rec.ks_record_field3.name])
                rec.ks_record_count = len(ks_records_grouped_data)
            elif rec.ks_record_count_type in ['sum', 'average'] and rec.ks_record_field and rec.ks_dashboard_item_type != 'ks_list_view':
                ks_records_grouped_data = rec.ks_fetch_model_data(rec.ks_model_name, rec.ks_domain, 'read_group', rec)
                if ks_records_grouped_data and len(ks_records_grouped_data) > 0:
                    ks_records_grouped_data = ks_records_grouped_data[0]
                    if rec.ks_record_count_type == 'sum' and ks_records_grouped_data.get('__count', False) and (
                            ks_records_grouped_data.get(rec.ks_record_field.name)):
                        rec.ks_record_count = ks_records_grouped_data.get(rec.ks_record_field.name, 0)
                    elif rec.ks_record_count_type == 'average' and ks_records_grouped_data.get(
                            '__count', False) and (ks_records_grouped_data.get(rec.ks_record_field.name)):
                        rec.ks_record_count = ks_records_grouped_data.get(rec.ks_record_field.name,
                                                                          0) / ks_records_grouped_data.get('__count',
                                                                                                           1)
                    else:
                        rec.ks_record_count = 0
                else:
                    rec.ks_record_count = 0
            else:
                rec.ks_record_count = 0
