from odoo import fields, models, api


class MCCCOdes(models.Model):
    _name = 'mcc.code.propay'
    _description = "MCC Codes"
    _order = "mcc_code_seq"

    mcc_code_seq = fields.Integer('Code Sequence')
    name = fields.Char('Code')
    merchant_type = fields.Char('Merchant Type')
    active = fields.Boolean(default=True)

    def name_get(self):
        result = []
        for mcc in self:
            name = "{} {}".format(mcc.name, mcc.merchant_type)
            result.append((mcc.id, name))
        return result


class BlueMaxPayAgreement(models.Model):
    _name = "bluemaxpay.agreement"
    _description = "BlueMaxPay Agreement"
    _order = "agreement_seq"

    agreement_seq = fields.Integer('Agreement Sequence')
    name = fields.Char('Agreement')
    heading = fields.Char('Agreement Heading')
    description = fields.Text('Agreement Description')
    active = fields.Boolean('Active', default=True)


class PropayDevice(models.Model):
    _name = "propay.device"
    _description = "Propay Device"
    _order = "device_seq"

    device_seq = fields.Integer('Device Sequence')
    name = fields.Char('Name')
    price = fields.Monetary('Price', currency_field='currency', tracking=True)
    currency = fields.Many2one("res.currency", string='Currency',
                               compute="_compute_company_currency", readonly=True)

    def _compute_company_currency(self):
        for rec in self:
            rec.currency = self.env.company.currency_id

    def get_device(self):
        pass


class PropayOrderDevice(models.Model):
    _name = "propay.order.device"
    _description = "Propay Order Device"
    _order = "o_device_seq"

    o_device_seq = fields.Integer('Order Device Sequence')
    name = fields.Char()
    user_id = fields.Many2one('res.users')
    device_id = fields.Many2one("propay.device")
    price = fields.Monetary('Price', currency_field='currency', related="device_id.price")
    currency = fields.Many2one('res.currency', string='Currency',
                               related="device_id.currency")


class PropayTier(models.Model):
    _name = 'propay.tier'
    _description = "ProPay tier"
    _order = "tier_seq"

    tier_seq = fields.Integer('Tier Sequence')
    name = fields.Char('Tier')
    active = fields.Boolean('Active', default=True)


class TimeZone(models.Model):
    _name = 'propay.timezone'
    _order = "timezone_seq"

    timezone_seq = fields.Integer('Timezone Sequence')
    name = fields.Char('Timezone', required=True)
    full_name = fields.Char("description")
    active = fields.Boolean('Active', default=True)


class PropayPage(models.Model):
    _name = 'propay.page'
    _rec_name = 'display_page'
    _description = "Page"
    _order = "page_seq"

    page_seq = fields.Integer('Page Sequence')
    display_page = fields.Char('Display Name')
    bluemaxpay_page = fields.Char('Page')
    active = fields.Boolean('Active', default=True)

class PropayTitlePage(models.Model):
    _name = 'propaytitle.page'
    _rec_name = 'display_name'
    _description = "Title Page"
    _order = "title_seq"

    title_seq = fields.Integer('Title Sequence')
    display_name = fields.Char('Display Name')
    propay_title = fields.Char('Propay Title')
    title_active = fields.Boolean('Active', default=True)

class AccountTypePage(models.Model):
    _name = 'account_type.page'
    _rec_name = 'account_type_display'
    _description = "Page"
    _order = "account_type_page_seq"

    account_type_page_seq = fields.Integer('Page Sequence')
    account_type_display = fields.Char('Display')
    account_type_bluemaxpay = fields.Char('ProPay Value')
    account_type_page_active = fields.Boolean('Active', default=True)


class PropayErrorCode(models.Model):
    _name = 'propay.error.codes'
    _rec_name = 'propay_value'
    _description = "Error Code"
    _order = "error_codes_seq"

    error_codes_seq = fields.Integer('Error Code Sequence')
    propay_status_code = fields.Char('Code')
    propay_value = fields.Char('Value')
    propay_notes = fields.Char('Notes')
    public_status_code = fields.Char('Public Status Code')


class MonthlyBankCardVolume(models.Model):
    _name = 'mbcv.value.propay'
    _description = "Monthly Bank Card Volume"
    _order = "mbc_code_seq"
    _rec_name = "monthly_bank_card_volume"

    mbc_code_seq = fields.Integer('MBC Sequence')
    monthly_number = fields.Char('Monthly Bank Card Volume')
    monthly_bank_card_volume = fields.Char('Description')
    active = fields.Boolean(default=True)


class AverageTicket(models.Model):
    _name = 'avg.ticket.propay'
    _description = "Average Ticket"
    _order = "avg_ticket_seq"
    _rec_name = "average_ticket"

    avg_ticket_seq = fields.Integer('Ticket Sequence')
    average_number = fields.Char('Average Ticket')
    average_ticket = fields.Char('Description')
    active = fields.Boolean(default=True)


class HighestTicket(models.Model):
    _name = 'highest.ticket.propay'
    _description = "Highest Ticket"
    _order = "highest_ticket_seq"
    _rec_name = "highest_ticket"

    highest_ticket_seq = fields.Integer('Ticket Sequence')
    highest_number = fields.Char('Highest Ticket')
    highest_ticket = fields.Char('Description')
    active = fields.Boolean(default=True)


class ResCountry(models.Model):
    _name = "country.code.propay"

    name = fields.Many2one('res.country')
    code = fields.Char('Country Code', related='name.code')
    propay_code = fields.Char('ProPay Code')
    active = fields.Boolean('Active', default=True)


class PartnerDevice(models.Model):
    _name = "partner.device"
    _description = "Partner Device"

    partner_id = fields.Many2one('res.partner')
    name = fields.Many2one('propay.device', "Device Name")
    nickname = fields.Char("Nickname")
    unique_device_id = fields.Char("Unique Device ID")
    license = fields.Char("License ID")
    site = fields.Char("Site ID")
    device_id = fields.Char("Device ID")
    serial_number = fields.Char()
    username = fields.Char()
    password = fields.Char()