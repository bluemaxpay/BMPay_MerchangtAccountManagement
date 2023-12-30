/** @odoo-module */

import { registry } from "@web/core/registry";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import { FormViewDialog } from '@web/views/view_dialogs/form_view_dialog';
import { useService } from "@web/core/utils/hooks";

import { Component } from "@odoo/owl";

export class SSOManagementComp extends Component {
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }
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
    }

}
SSOManagementComp.props = {
    ...standardWidgetProps,
};
SSOManagementComp.template = "sso_management";

export const SSOManagement = {
    component: SSOManagementComp,
};
registry.category("view_widgets").add("sso_management", SSOManagement);
