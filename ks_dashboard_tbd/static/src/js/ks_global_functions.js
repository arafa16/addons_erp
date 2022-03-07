odoo.define('ks_dashboard_ninja.KsGlobalFunction', function (require) {
"use strict";
var session = require('web.session')

return {

        ksNumFormatter: function (num, digits) {
            var negative;
            var si = [{
                    value: 1,
                    symbol: ""
                },
                {
                    value: 1E3,
                    symbol: "t"
                    // thousand
                },
                {
                    value: 1E6,
                    symbol: "M"
                    // million
                },
                {
                    value: 1E9,
                    symbol: "B"
                    // billion
                },
                {
                    value: 1E12,
                    symbol: "T"
                    // trillion

                },
                {
                    value: 1E15,
                    symbol: "Q"
                    // quadrillion
                },
                {
                    value: 1E18,
                    symbol: "E"
                    // quintillion
                }
            ];
            if(num<0){
                num = Math.abs(num)
                negative = true
            }
            var rx = /\.0+$|(\.[0-9]*[1-9])0+$/;
            var i;
            for (i = si.length - 1; i > 0; i--) {
                if (num >= si[i].value) {
                    break;
                }
            }
            if(negative){
                return "-" +(num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }else{
                return (num / si[i].value).toFixed(digits).replace(rx, "$1") + si[i].symbol;
            }
        },
         ks_monetary: function(value,currency_id){
            var currency = session.get_currency(currency_id);
            if (!currency) {
                return value;
            }
            if (currency.position === "after") {
                return value += ' ' + currency.symbol;
            } else {
                return currency.symbol + ' ' + value;
            }
        },

}
})
