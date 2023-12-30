/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";
import { jsonrpc } from "@web/core/network/rpc_service";
import { BlockUI } from "@web/core/ui/block_ui";


publicWidget.registry.ProPay = publicWidget.Widget.extend({
    selector: ".oe_website_login_container",
    events:{
        'change .field-checkbox': '_onChangeMerchantAccount',
        'change .pro-agreement': '_onChangeAgreement',
        'click .print-agreement-propay': '_onClickPrint',
        'change .device': '_onChangeDevice',
        'change select[name="country"]': '_onChangeCountry',
        'submit .oe_signup_form_propay_1': '_onClickSubmit',
    },

    init: function() {
        var heartland = $('#agreement-heartland').is(":checked");
        var propay = $('#agreement-propay').is(":checked");
        $('#btn-submit-propay-heartland').hide()
        return this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");
    },
    start: function() {
        var heartland = $('#agreement-heartland').is(":checked");
        var propay = $('#agreement-propay').is(":checked");
        $('#btn-submit-propay-heartland').hide()
        return this._super.apply(this, arguments);
    },
    _onClickPrint: function(){
        jsonrpc('/propay/agreement/download', {});
    },
    _onChangeAgreement: function(){
        var agreement_bluemaxpay = $('input[name="agreement"]:checked');
        jsonrpc('/get/bluemax/agreement', {}).then(function (result) {
            if (agreement_bluemaxpay.length == result){
                $('#btn-submit-propay-heartland').show()
            } else {
                $('#btn-submit-propay-heartland').hide()
            }
        });
    },
    _onChangeDevice: function() {
        var $device = this.$('select[name="device"]');
        this.rpc.query({
            route: '/propay/device/',
            params: {
                'id': $device.val(),
            },
        }).then((device) => {
            if (device == 'Secure Submit'){
                $('.propay-secure').hide()
            }
            if (device != 'Secure Submit'){

                $('.propay-secure').show()
            }
        });
    },
    _onChangeCountry: function(){
        var country = this.$('select[name="country"]');
        var CountryCode = (country.val());
        jsonrpc('/get/blumaxpay/country_code', {
            'CountryCode': CountryCode
        }).then(function (country_states) {
            var state = $('#state').html()
            var data_html = '<label for="state" >State<a style="color: red;">*</a></label></br><select name="state" class="form-control state">'
            data_html += '<option>States...</option>'
            for (var i = 0; i < country_states.length; ++i) {
                data_html += '<option class="state" value="' + country_states[i].code + '">'
                data_html += country_states[i].name
                data_html += '</option>'
            }
            data_html += '</select>'
            $('#state').html(data_html);
        });
    },
    _onChangeMerchantAccount: function () {
        var self = this;
        var checkbox = $('#checkbox').is(":checked");

    },
    _onClickSubmit: function(event){
        this.call('ui', 'block', {
            'message': _t("Please wait while we process your information."),
        });
    },
});
