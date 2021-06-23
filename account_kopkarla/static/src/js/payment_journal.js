odoo.define('account_kopkarla.payment', function(require) {
    "use strict";

//    alert('hypur')
//    console.log('hypur aaa');

    var Widget = require('web.Widget');

    var Counter = Widget.extend({
        template: 'account_kopkarla.btn_test',
        events: {
            'click button': '_onClick',
        },
        init: function (parent, value) {
            this._super(parent);
            this.count = value;
        },
        _onClick: function () {
            this.count++;
            this.$('.val').text(this.count);
//            console.log(this.count);
        },
    });
});
