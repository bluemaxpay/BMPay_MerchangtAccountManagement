/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MerchantAccount = publicWidget.Widget.extend({
    selector: ".device_order",
    events:{
        'change select[name="device"]': '_onChangeDevice',
    },
    init: function () {
        this._super.apply(this, arguments);
        this.orm = this.bindService("orm");
    },
    _onChangeDevice: async function(){
        var $device = this.$('select[name="device"]');
        var DeviceID = ($device.val() || 0);
        var result = await this.orm.call('propay.device', 'search_read', [], {domain: [['id', '=', DeviceID]]})
        var price = $('#price').html()
        $('#price').html('<label for="price">Price:</label><input type="text" id="price" class="form-control" value="' + result[0].price + '" name="price"required="required"/>');
    }
});

publicWidget.registry.MerchantSSO = publicWidget.Widget.extend({
    selector: ".single-sign-on",
    events:{
        'change select[name="bluemaxpay_page"]': '_onChangePage',
    },
    init: function() {
        $('#TransactionNumber').hide()
        $('#TransactionReportId').hide()
        this._super.apply(this, arguments);
    },
    _onChangePage: function(){
        $.getJSON("https://api.ipify.org?format=json", function(data) {
            $("#ip_addresss").html('<input type="hidden" id="ip" class="form-control" value="' + data.ip + '" name="ip"/>');
        })
        var $bluemaxpay_page = this.$('select[name="bluemaxpay"]');
        var Page = ($bluemaxpay_page.val() || 0);
        if (Page == 'Report/TransactionDetails'){
            $('#TransactionNumber').show()
            $('#TransactionReportId').show()

        } else{
            $('#TransactionNumber').hide()
            $('#TransactionReportId').hide()
        }
    },
});
