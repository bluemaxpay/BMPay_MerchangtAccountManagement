/** @odoo-module */

import { FormRenderer } from '@web/views/form/form_renderer';
import { FormViewDialog } from '@web/views/view_dialogs/form_view_dialog';

import { useService } from "@web/core/utils/hooks";
import { patch } from '@web/core/utils/patch';

patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    },
    async _onClickSSO(){
        var response = await $.getJSON("https://api.ipify.org?format=json");
        var ipAddress = response.ip;
        this.dialogService.add(FormViewDialog, {
            resModel: "single.sign.on",
            context: {
                default_ip_address: ipAddress,
                default_user_id: this.props.record.data.id,
                active_id: this.props.record.data.id,
                active_model: 'res.users',
            },
            title: "SSO Management",
            onRecordSaved: () => this._onDialogSaved(),
        });
    },
    _onDialogSaved(){
        alert("HELLO")
    },
});
