from odoo import _, api, fields, models
# from odoo.exceptions import UserError

# from .expression_evaluator import ExpressionEvaluator
# from .accounting_none import AccountingNone

SRC_BUDGET = "budgets"
SRC_ACHIEVEMENT = "achievement"


# class AutoStruct(object):
#     def __init__(self, **kwargs):
#         for k, v in kwargs.items():
#             setattr(self, k, v)


# class MisReport(models.Model):
#     _inherit = "mis.report"
#
#     def _declare_and_compute_period(
#         self,
#         expression_evaluator,
#         kpi_matrix,
#         col_key,
#         col_label,
#         col_description,
#         subkpis_filter=None,
#         get_additional_query_filter=None,
#         locals_dict=None,
#         no_auto_expand_accounts=False,
#         is_budget=False,
#     ):
#         """ Evaluate a report for a given period, populating a KpiMatrix.
#
#         :param expression_evaluator: an ExpressionEvaluator instance
#         :param kpi_matrix: the KpiMatrix object to be populated created
#                            with prepare_kpi_matrix()
#         :param col_key: the period key to use when populating the KpiMatrix
#         :param subkpis_filter: a list of subkpis to include in the evaluation
#                                (if empty, use all subkpis)
#         :param get_additional_query_filter: a bound method that takes a single
#                                             query argument and returns a
#                                             domain compatible with the query
#                                             underlying model
#         :param locals_dict: personalized locals dictionary used as evaluation
#                             context for the KPI expressions
#         :param no_auto_expand_accounts: disable expansion of account details
#         """
#         self.ensure_one()
#
#         # prepare the localsdict
#         if locals_dict is None:
#             locals_dict = {}
#
#         # Evaluate subreports
#         for subreport in self.subreport_ids:
#             subreport_locals_dict = subreport.subreport_id._evaluate(
#                 expression_evaluator, subkpis_filter, get_additional_query_filter,
#             )
#             locals_dict[subreport.name] = AutoStruct(
#                 **{
#                     srk.name: subreport_locals_dict.get(srk.name, AccountingNone)
#                     for srk in subreport.subreport_id.kpi_ids
#                 }
#             )
#
#         locals_dict.update(self.prepare_locals_dict())
#         locals_dict["date_from"] = fields.Date.from_string(
#             expression_evaluator.date_from
#         )
#         locals_dict["date_to"] = fields.Date.from_string(expression_evaluator.date_to)
#
#         # fetch non-accounting queries
#         locals_dict.update(
#             self._fetch_queries(
#                 expression_evaluator.date_from,
#                 expression_evaluator.date_to,
#                 get_additional_query_filter,
#             )
#         )
#
#         # use AEP to do the accounting queries
#         if is_budget:
#             expression_evaluator.aep_do_queries()
#         else:
#             expression_evaluator.aep_do_queries()
#
#         self._declare_and_compute_col(
#             expression_evaluator,
#             kpi_matrix,
#             col_key,
#             col_label,
#             col_description,
#             subkpis_filter,
#             locals_dict,
#             no_auto_expand_accounts,
#         )


class MisReportInstance(models.Model):
    _inherit = "mis.report.instance"

    def _add_column(self, aep, kpi_matrix, period, label, description):
        if period.source == SRC_BUDGET or period.source == SRC_ACHIEVEMENT :
            budget = period.source
            return self._add_column_move_lines(aep, kpi_matrix, period, label, description, budget)
        else:
            return super(MisReportInstance, self)._add_column(aep, kpi_matrix, period, label, description)

    # def _add_column_move_lines(self, aep, kpi_matrix, period, label,   description, is_budget=False):
    #     if not period.date_from or not period.date_to:
    #         raise UserError(
    #             _("Column %s with move lines source must have from/to dates.")
    #             % (period.name,)
    #         )
    #     expression_evaluator = ExpressionEvaluator(
    #         aep,
    #         period.date_from,
    #         period.date_to,
    #         None,  # target_move now part of additional_move_line_filter
    #         period._get_additional_move_line_filter(),
    #         period._get_aml_model_name(),
    #     )
    #     self.report_id._declare_and_compute_period(
    #         expression_evaluator,
    #         kpi_matrix,
    #         period.id,
    #         label,
    #         description,
    #         period.subkpi_ids,
    #         period._get_additional_query_filter,
    #         no_auto_expand_accounts=self.no_auto_expand_accounts,
    #         is_budget=is_budget,
    #     )


class MisReportInstancePeriod(models.Model):
    _inherit = "mis.report.instance.period"

    source = fields.Selection(selection_add=[(SRC_BUDGET, "Budgets"), (SRC_ACHIEVEMENT, "Achievement"),])
