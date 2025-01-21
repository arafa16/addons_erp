from odoo import api, models, _


class ProductTemplate(models.Model):
    _inherit = "product.product"

    # @api.multi
    # def name_get(self):
    #     self.read(['name', 'default_code'])
    #     # return [(template.id, '%s%s' % (template.default_code and '[%s] ' % template.default_code or '', template.name))
    #     return [(template.id, '%s%s' % (template.product_tmpl_id.can_be_expensed and '[%s] ' % template.product_tmpl_id.property_account_expense_id.code or
    #                                    (template.default_code and '[%s] ' % template.default_code or ''), template.name))
    #             for template in self]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        def _name_search_expense(name):
            # Product = self.env['product.product']
            # templates = self.browse([])
            # products_ns = Product.search([('can_be_expensed', '=', True)])
            # # products = Product.browse([x[0] for x in products_ns])
            # for x in products_ns:
            #     if name in x.product_tmpl_id.name.lower() or name in x.product_tmpl_id.default_code.lower():
            #         templates |= x
            # for x in products_ns:
            #     if x.product_tmpl_id.property_account_expense_id and name in x.product_tmpl_id.property_account_expense_id.code:
            #         templates |= x
            # templates |= products.mapped('product_tmpl_id')
                # if (not products) or (limit and (len(templates) > limit)):
                #     break

            # re-apply product.template order + name_get
            # return super(ProductTemplate, self).name_search(
            #     '', args=[('id', 'in', list(set(templates.ids)))],
            #     operator='ilike', limit=limit)
            return super(ProductTemplate, self).name_search(
                '', args=[('can_be_expensed', '=', True), '|', ('name', 'ilike', name), ('default_code', 'ilike', name)],
                operator='ilike', limit=limit)
        if args:
            for term in (args or []):
                if term == ['can_be_expensed', '=', True]:
                    return _name_search_expense(name)
                else:
                    return super(ProductTemplate, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return super(ProductTemplate, self).name_search(name=name, args=args, operator=operator, limit=limit)