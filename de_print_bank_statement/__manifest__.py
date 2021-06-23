# -*- coding: utf-8 -*-
#################################################################################
# Author      : Dynexcel (<https://dynexcel.com/>)
# Copyright(c): 2015-Present dynexcel.com
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
#################################################################################
{
  "name"                 :  "Print Bank Statement",
  "summary"              :  "This App will Add Print Option in Cash/Bank Statement",
  "category"             :  "Accounting",
  "version"              :  "1.3",
  "sequence"             :  1,
  "author"               :  "Dynexcel",
  "license"              :  "OPL-1",
  "website"              :  "http://dynexcel.com",
  "description"          :  """
This App will Add Print Option in Cash/Bank Statement
""",
  "live_test_url"        :  "",
  "depends"              :  [
                             'account'
                            ],
  "data"                 :  [
                             'views/statement_report.xml',
                            ],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  0,
  "currency"             :  "EUR",
  "images"		 :['static/description/banner.jpg'],
}