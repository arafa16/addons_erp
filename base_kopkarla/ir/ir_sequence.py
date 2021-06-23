from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import pytz

FORMATROMAN = (
    ('M', 1000),
    ('CM', 900),
    ('D', 500),
    ('CD', 400),
    ('C', 100),
    ('XC', 90),
    ('L', 50),
    ('XL', 40),
    ('X', 10),
    ('IX', 9),
    ('V', 5),
    ('IV', 4),
    ('I', 1)
)

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_prefix_suffix(self):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _convert_to_roman(n):
            result = ""
            for numeral, integer in FORMATROMAN:
                while n >= integer:
                    result += numeral
                    n -= integer
            return result

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if self._context.get('ir_sequence_date'):
                effective_date = datetime.strptime(self._context.get('ir_sequence_date'), '%Y-%m-%d')
            if self._context.get('ir_sequence_date_range'):
                range_date = datetime.strptime(self._context.get('ir_sequence_date_range'), '%Y-%m-%d')

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S',
                'rom_year': '%Y', 'rom_month': '%m', 'rom_day': '%d', 'rom_y': '%y', 'rom_doy': '%j', 'rom_woy': '%W',
                'rom_weekday': '%w', 'rom_h24': '%H', 'rom_h12': '%I', 'rom_min': '%M', 'rom_sec': '%S'
            }
            res = {}
            for key, format in sequences.items():
                res[key] = 'rom_' not in key and effective_date.strftime(format) or _convert_to_roman(int(effective_date.strftime(format)))
                res['range_' + key] = 'rom_' not in key and range_date.strftime(format) or _convert_to_roman(int(range_date.strftime(format)))
                res['current_' + key] = 'rom_' not in key and now.strftime(format) or _convert_to_roman(int(now.strftime(format)))

            return res

        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % (self.get('name')))
        return interpolated_prefix, interpolated_suffix
