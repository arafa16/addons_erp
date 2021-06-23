# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import split_every
from psycopg2 import OperationalError

from odoo import api, fields, models, registry, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_round

from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class ProcurementRule(models.Model):
    """ A rule describe what a procurement should do; produce, buy, move, ... """
    _inherit = 'procurement.rule'

    def _run_move(self, product_id, product_qty, product_uom, location_id, name, origin, values):
        if not self.location_src_id:
            msg = _('No source location defined on procurement rule: %s!') % (self.name, )
            raise UserError(msg)

        # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
        # Search if picking with move for it exists already:
        group_id = False
        if self.group_propagation_option == 'propagate':
            group_id = values.get('group_id', False) and values['group_id'].id
        elif self.group_propagation_option == 'fixed':
            group_id = self.group_id.id

        data = self._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        # Since action_confirm launch following procurement_group we should activate it.
        move = self.env['stock.move'].sudo().with_context(force_company=data.get('company_id', False)).create(data)
        move.update({'cost_center_id': values.get('cost_center_id', False), 'analytic_account_id': values.get('analytic_account_id', False)})
        move._action_confirm()
        return True