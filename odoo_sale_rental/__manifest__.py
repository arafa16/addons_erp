# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# License URL : https://store.webkul.com/license.html/
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################

{
  "name"                 :  "Odoo Rental Sale",
  "summary"              :  "Enable rental selling feature in odoo.",
  "category"             :  "Website",
  "version"              :  "1.0.0",
  "sequence"             :  1,
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/Odoo-Rental-Sale.html",
  "description"          :  """ https://webkul.com/blog/odoo-rental-sale/ ,Odoo Rental Sale, Odoo rental Management""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=odoo_sale_rental&version=11.0&lifetime=60&lout=1&custom_url=/",
  "depends"              :  [
                              'sale_stock',
                              'sale_management',
                              'enhanced_sales_attribute'
                            ],
  "data"                 :  [
                            'security/rental_sale_security.xml',
                            'security/ir.model.access.csv',
                            'data/product_uom_rental_data.xml',
                            'data/rental_reason_data.xml',
                            'data/product_demo.xml',
                            'data/rental_cron.xml',
                            'data/ir_sequence_data.xml',
                            'wizard/rental_order_transient_view.xml',
                            'wizard/renew_rental_order_transient_view.xml',
                            'wizard/rental_reason_transient_view.xml',
                            'views/rental_product_view.xml',
                            'views/rental_view.xml',
                            'views/rental_order_view.xml',
                            'views/rental_menu_view.xml',
                            'views/inherited_sale_order_views.xml',
                            'views/inherit_picking_view.xml',
                            'views/res_config_settings_views.xml',
                            ],
  "images"               :  ['static/description/Banner.png'],
  "application"          :  False,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}
