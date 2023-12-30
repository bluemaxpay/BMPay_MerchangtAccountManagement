from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    class_str = fields.Char('ClassStr', related='company_id.class_str', readonly=False)
    device_str = fields.Char('DeviceStr', related='company_id.device_str', readonly=False)
    cert_str = fields.Char('CertStr', related='company_id.cert_str', readonly=False)
    term_id = fields.Char('TermId', related='company_id.term_id', readonly=False)
    x509_cert = fields.Binary('X509 Certificate', related='company_id.x509_cert', readonly=False)
    propay_logo = fields.Binary('Propay Logo', related='company_id.propay_logo', readonly=False)
    notification_email = fields.Char('Notification Email', related='company_id.notification_email', readonly=False)

    tier = fields.Selection([('Test', 'Test'), ('Merchant', 'Merchant')],
                            default='Test', related='company_id.tier', readonly=False)

    secret_api_key = fields.Char('Secret Api Key', related='company_id.secret_api_key', readonly=False)
    developer_id = fields.Char('Developer', related='company_id.developer_id', readonly=False)
    version_number = fields.Char('Version Number', related='company_id.version_number', readonly=False)

    api_url = fields.Char('Api URL', related='company_id.api_url', readonly=False)
    api_signup_url = fields.Char('Api Signup URL', related='company_id.api_signup_url', readonly=False)
    propay_tier_id = fields.Many2one('propay.tier', string="Default Tier", related='company_id.propay_tier_id', readonly=False)
    propay_device_id = fields.Many2one('propay.device', string="Default Device", related='company_id.propay_device_id', readonly=False)

    upload_document = fields.Boolean(related='company_id.upload_document', readonly=False)
    edit_bank_details = fields.Boolean(related='company_id.edit_bank_details', readonly=False)
    edit_address_details = fields.Boolean(related='company_id.edit_address_details', readonly=False)
    beneficial_ownership_count = fields.Boolean(related='company_id.beneficial_ownership_count', readonly=False)
    beneficial_ownership_data = fields.Boolean(related='company_id.beneficial_ownership_data', readonly=False)
    ach_transaction = fields.Boolean(related='company_id.ach_transaction', readonly=False)
    order = fields.Boolean(related='company_id.order', readonly=False)
    merchant_account_management = fields.Boolean(related='company_id.merchant_account_management', readonly=False)
    # change_merchant_account_password = fields.Boolean(related='company_id.change_merchant_account_password', readonly=False)

    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        class_str = params('bluemaxpay_account_management.class_str')
        device_str = params('bluemaxpay_account_management.device_str')
        cert_str = params('bluemaxpay_account_management.cert_str')
        term_id = params('bluemaxpay_account_management.term_id')
        x509_cert = params('bluemaxpay_account_management.x509_cert')
        propay_logo = params('bluemaxpay_account_management.propay_logo')
        tier = params('bluemaxpay_account_management.tier')
        notification_email = params('bluemaxpay_account_management.notification_email')
        secret_api_key = params('bluemaxpay_account_management.secret_api_key')
        version_number = params('bluemaxpay_account_management.version_number')
        developer_id = params('bluemaxpay_account_management.developer_id')
        api_url = params('bluemaxpay_account_management.api_url')
        api_signup_url = params('bluemaxpay_account_management.api_signup_url')
        res.update(
            class_str=class_str,
            device_str=device_str,
            cert_str=cert_str,
            term_id=term_id,
            x509_cert=x509_cert,
            propay_logo=propay_logo,
            tier=tier,
            notification_email=notification_email,
            secret_api_key=secret_api_key,
            version_number=version_number,
            developer_id=developer_id,
            api_url=api_url,
            api_signup_url=api_signup_url,
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.class_str', self.class_str)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.device_str', self.propay_device_id and self.propay_device_id.name or False)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.cert_str', self.cert_str)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.term_id', self.term_id)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.x509_cert', self.x509_cert)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.propay_logo', self.propay_logo)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.tier', self.tier)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.notification_email', self.notification_email)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.secret_api_key', self.secret_api_key)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.version_number', self.version_number)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.developer_id', self.developer_id)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.api_url', self.api_url)
        self.env['ir.config_parameter'].sudo().set_param(
            'bluemaxpay_account_management.api_signup_url', self.api_signup_url)
