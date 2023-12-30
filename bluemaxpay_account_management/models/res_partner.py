from odoo import fields, models, api


class Partner(models.Model):
    _inherit = "res.partner"

    def decode_bank_details(self):
        user = self.env.user
        for partner in self:
            partner.decoded_account_country_code = partner.account_country_code and user.decrypt_data(partner.account_country_code) or False
            partner.decoded_routing_number = partner.routing_number and user.decrypt_data(partner.routing_number) or False
            partner.decoded_account_ownership_type = partner.account_ownership_type and user.decrypt_data(partner.account_ownership_type) or False
            partner.decoded_bank_name = partner.bank_name and user.decrypt_data(partner.bank_name) or False
            partner.decoded_account_type = partner.account_type and user.decrypt_data(partner.account_type) or False
            bank_account_number = False
            if partner.bank_account_number:
                decoded_bank_account_number = user.decrypt_data(partner.bank_account_number)
                bank_account_number = "{}{}".format(user.encrypt_data(decoded_bank_account_number[:-4]),
                                                    decoded_bank_account_number[-4:])
            partner.decoded_bank_account_number = bank_account_number

    is_merchant = fields.Boolean('Is Merchant')

    account_country_code = fields.Char('Account Country Code', readonly=True)
    bank_account_number = fields.Char('Bank Account Number', readonly=True)
    routing_number = fields.Char('Routing Number', readonly=True)
    account_ownership_type = fields.Char('Account Ownership Type', readonly=True)
    bank_name = fields.Char('Bank Name', readonly=True)
    account_type = fields.Char('Account Type', readonly=True)

    decoded_account_country_code = fields.Char('Account Country Code', compute="decode_bank_details")
    decoded_bank_account_number = fields.Char('Bank Account Number', compute="decode_bank_details")
    decoded_routing_number = fields.Char('Routing Number', compute="decode_bank_details")
    decoded_account_ownership_type = fields.Char('Account Ownership Type', compute="decode_bank_details")
    decoded_bank_name = fields.Char('Bank Name', compute="decode_bank_details")
    decoded_account_type = fields.Char('Account Type', compute="decode_bank_details")

    propay_apartment_number = fields.Char('Apartment Number', readonly=True)
    propay_address = fields.Char('Address', readonly=True)
    propay_city = fields.Char('City', readonly=True)
    propay_state = fields.Char('State', readonly=True)
    propay_country = fields.Char('Country', readonly=True)
    propay_zip = fields.Char('Zip', readonly=True)

    first_name = fields.Char('First Name', readonly=True)
    last_name = fields.Char('Last Name', readonly=True)
    initial = fields.Char('Initial', readonly=True)
    day_phone = fields.Char('Day Phone', readonly=True)
    even_phone = fields.Char('Even Phone', readonly=True)

    partner_device_ids = fields.One2many('partner.device', 'partner_id')
