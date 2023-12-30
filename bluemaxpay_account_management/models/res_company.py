from odoo import fields, models, api, _


class ResCompany(models.Model):
    _inherit = "res.company"

    propay_tier_id = fields.Many2one('propay.tier', string="Default Tier")
    propay_device_id = fields.Many2one('propay.device', string="Default Device")
    upload_document = fields.Boolean()
    edit_bank_details = fields.Boolean()
    edit_address_details = fields.Boolean()
    beneficial_ownership_count = fields.Boolean()
    beneficial_ownership_data = fields.Boolean()
    ach_transaction = fields.Boolean()
    order = fields.Boolean()
    merchant_account_management = fields.Boolean()
    class_str = fields.Char('ClassStr')
    device_str = fields.Char('DeviceStr')
    cert_str = fields.Char('CertStr')
    term_id = fields.Char('TermId')
    x509_cert = fields.Binary('X509 Certificate')
    propay_logo = fields.Binary('Propay Logo')
    notification_email = fields.Char('Notification Email')

    tier = fields.Selection([('Test', 'Test'), ('Merchant', 'Merchant')],
                            default='Test')

    secret_api_key = fields.Char('Secret Api Key')
    developer_id = fields.Char('Developer')
    version_number = fields.Char('Version Number')

    api_url = fields.Char('Api URL')
    api_signup_url = fields.Char('Api Signup URL')
