from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import json
import requests


class MerchantAccountManagement(models.TransientModel):
    _name = "merchant.account.management"

    name = fields.Char('Name')
    user_id = fields.Many2one('res.users')
    select = fields.Selection([('upload', 'Upload'), ('edit_bank', 'Edit Bank Details'),
                               ('address', 'Edit Merchant Address'), ('renewal', 'Renewal'),
                               ('owner_count', 'Beneficial Owner Count'), ('owner_data', 'Beneficial Owner Data'),
                               ('affiliation', 'Remove Affiliation'), ('order', 'Order')])

    def upload_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Upload Account',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'document.upload',
            'context': {
                'default_account_number': self.user_id.account_number,
            }
        }

    def edit_bank(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bank Details',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'propay.bank.account',
            'context': {
                'default_user_id': self.user_id.id,
                'default_account_country_code': self.user_id.decrypt_data(
                    self.user_id.partner_id.account_country_code),
                'default_bank_account_number': self.user_id.decrypt_data(
                    self.user_id.partner_id.bank_account_number),
                'default_routing_number': self.user_id.decrypt_data(
                    self.user_id.partner_id.routing_number),
                'default_account_ownership_type': self.user_id.decrypt_data(
                    self.user_id.partner_id.account_ownership_type),
                'default_bank_name': self.user_id.decrypt_data(
                    self.user_id.partner_id.bank_name),
                'default_account_type': self.user_id.decrypt_data(
                    self.user_id.partner_id.account_type)
            }
        }

    def edit_account_details(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Merchant Account',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'propay.account.address',
            'context': {
                'default_user_id': self.user_id.id,
                'default_first_name': self.user_id.partner_id.first_name,
                'default_last_name': self.user_id.partner_id.last_name,
                'default_initial': self.user_id.partner_id.initial,
                'default_day_phone': self.user_id.partner_id.day_phone,
                'default_even_phone': self.user_id.partner_id.even_phone,
                'default_email': self.user_id.partner_id.email
            }
        }

    def renewal_account(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renewal Account',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'renew.account',
            'context': {
                'default_account_number': self.user_id.account_number
            }
        }

    def owner_count(self):
        self.user_id.update_beneficial_owner_count()
    def beneficial_owner_data(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Beneficial Owner Data',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'beneficial.data',
            'context': {
                'default_user_id': self.user_id.id,
            }
        }

    def remove_affiliation(self):
        self.user_id.remove_affiliation()

    def create_order(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Order',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'order.device',
            'context': {
                'default_user_id': self.user_id.id,
            }
        }
    def select_type(self):
        if self.select == 'upload':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Document Upload Account',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'document.upload',
                'context': {
                    'default_account_number': self.user_id.account_number,
                }
            }
        if self.select == 'edit_bank':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bank Details',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'propay.bank.account',
                'context': {
                    'default_user_id': self.user_id.id,
                    'default_account_country_code': self.user_id.decrypt_data(self.user_id.partner_id.account_country_code),
                    'default_bank_account_number': self.user_id.decrypt_data(self.user_id.partner_id.bank_account_number),
                    'default_routing_number': self.user_id.decrypt_data(self.user_id.partner_id.routing_number),
                    'default_account_ownership_type': self.user_id.decrypt_data(self.user_id.partner_id.account_ownership_type),
                    'default_bank_name': self.user_id.decrypt_data(self.user_id.partner_id.bank_name),
                    'default_account_type': self.user_id.decrypt_data(self.user_id.partner_id.account_type)
                }
            }
        if self.select == 'address':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Merchant Account',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'propay.account.address',
                'context': {
                    'default_user_id': self.user_id.id,
                    'default_first_name': self.user_id.partner_id.first_name,
                    'default_last_name': self.user_id.partner_id.last_name,
                    'default_initial': self.user_id.partner_id.initial,
                    'default_day_phone': self.user_id.partner_id.day_phone,
                    'default_even_phone': self.user_id.partner_id.even_phone,
                    'default_email': self.user_id.partner_id.email
                }
            }
        if self.select == 'renewal':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Renewal Account',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'renew.account',
                'context': {
                    'default_account_number': self.user_id.account_number
                }
            }
        if self.select == 'owner_count':
            self.user_id.update_beneficial_owner_count()
        if self.select == 'owner_data':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Beneficial Owner Data',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'beneficial.data',
                'context': {
                    'default_user_id': self.user_id.id,
                }
            }
        if self.select == 'affiliation':
            self.user_id.remove_affiliation()
        if self.select == 'order':
            return {
                'type': 'ir.actions.act_window',
                'name': 'Order',
                'view_mode': 'form',
                'target': 'new',
                'res_model': 'order.device',
                'context': {
                    'default_user_id': self.user_id.id,
                }
            }


class DocumentUplaod(models.Model):
    _name = 'create.merchant'
    _description = 'merchant'

    name = fields.Char('First Name')
    user_id = fields.Many2one('res.users')
    last_name = fields.Char('Last Name')
    initial = fields.Char('Initial')
    date_of_birth = fields.Date('Date of Birth')

    # Address
    apartment_number = fields.Char('Apartment Number')
    address = fields.Char('Address')
    city = fields.Char('City')
    state = fields.Char('State')
    state_id = fields.Many2one('res.country.state', string='State')
    country = fields.Char('Country')
    country_id = fields.Many2one('country.code.propay', string='Country')
    res_country_id = fields.Many2one('res.country', related="country_id.name")
    zip = fields.Char('Zip')
    day_phone = fields.Char('Day Phone')
    even_phone = fields.Char('Even Phone')

    # Bank Account
    account_country_code_id = fields.Many2one('country.code.propay', string='Account Country Code')
    routing_number = fields.Char('Routing Number')
    account_ownership_type = fields.Selection([('Personal', 'Personal'), ('Business', 'Business')], string='Account Ownership Type')
    bank_account_number = fields.Char('Bank Account Number')
    bank_name = fields.Char('Bank Name')
    account_type_id = fields.Many2one('account_type.page', string='Account Type',
                                      domain=[('account_type_page_active', '=', True)])

    # Business Data
    business_legal_name = fields.Char('Business Legal Name')
    doing_business_as = fields.Char('Doing Business As')
    business_description = fields.Char('Business Description')
    ein = fields.Char('EIN')
    # monthly_card_volume = fields.Char('Monthly Card Volume')
    monthly_card_volume_id = fields.Many2one('mbcv.value.propay', string='Monthly Bank Card Volume')
    average_ticket_id = fields.Many2one('avg.ticket.propay', string='Average Ticket')
    highest_ticket_id = fields.Many2one('highest.ticket.propay', string='Highest Ticket')
    social_security_number = fields.Char('Social Security Number')
    website_url = fields.Char('Website URL')
    mcc_code_id = fields.Many2one('mcc.code.propay', string="MCC Code")

    # Card Details
    time_zone_id = fields.Many2one('propay.timezone', 'Time Zone')
    tier_id = fields.Many2one('propay.tier', 'Tier')
    currency_code_id = fields.Many2one('res.currency', 'Currency Code')

    # login info
    account_number = fields.Char()
    username = fields.Char()
    password = fields.Char()

    def create_merchant(self):
        self.ensure_one()
        self.user_id.create_merchant_wizard_id = self.id

    # def create_merchant(self):
    #     class_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
    #     if not class_str:
    #         raise UserError('Add Class String for ProPay')
    #
    #     device_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
    #     if not device_str:
    #         raise UserError('Add Device String for ProPay')
    #
    #     cert_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
    #     term_id = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
    #     if not cert_str and not term_id:
    #         raise UserError('Add authentication credentials for ProPay')
    #     date_of_birth = ''
    #     url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_signup_url')
    #
    #     # certStr = 'c095ada626244a6982e83f480787ae:0787ae'
    #     certStr = cert_str + ':' + term_id
    #
    #     certStr_bytes = certStr.encode('ascii')
    #     certStr_base64_bytes = base64.b64encode(certStr_bytes)
    #     base64_certStr = certStr_base64_bytes.decode('ascii')
    #     payload = json.dumps({
    #         "PersonalData": {
    #             "FirstName": self.name,
    #             "MiddleInitial": self.initial,
    #             "LastName": self.last_name,
    #             "DateOfBirth": str(self.date_of_birth),
    #             "SocialSecurityNumber": self.social_security_number,
    #             "SourceEmail": self.user_id.login,
    #             "PhoneInformation": {
    #                 "DayPhone": self.day_phone,
    #                 "EveningPhone": self.even_phone
    #             },
    #             "NotificationEmail": self.user_id.login,
    #             "TimeZone": self.time_zone
    #         },
    #         "SignupAccountData": {
    #             "CurrencyCode": self.currency_code,
    #             "Tier": self.tier
    #         },
    #         "BusinessData": {
    #             "BusinessLegalName": self.business_legal_name,
    #             "DoingBusinessAs": self.doing_business_as,
    #             "EIN": self.ein,
    #             "MerchantCategoryCode": "5999",
    #             "WebsiteURL": "http://Propay.com",
    #             "BusinessDescription": self.business_description,
    #             "MonthlyBankCardVolume": self.monthly_card_volume,
    #             "AverageTicket": self.average_ticket,
    #             "HighestTicket": self.highest_ticket
    #         },
    #         "Address": {
    #             "ApartmentNumber": self.apartment_number,
    #             "Address1": self.address,
    #             "Address2": "Suite 200",
    #             "City": self.city,
    #             "State": self.state,
    #             "Country": self.country,
    #             "Zip": self.zip
    #         },
    #         "BusinessAddress": {
    #             "ApartmentNumber": self.apartment_number,
    #             "Address1": self.address,
    #             "Address2": "SW",
    #             "City": self.city,
    #             "State": self.state,
    #             "Country": self.country,
    #             "Zip": self.zip
    #         },
    #         "BankAccount": {
    #             "AccountCountryCode": self.account_country_code,
    #             "BankAccountNumber": self.bank_account_number,
    #             "RoutingNumber": self.routing_number,
    #             "AccountOwnershipType": self.account_ownership_type,
    #             "BankName": self.bank_name,
    #             "AccountType": self.account_type,
    #             "AccountName": None,
    #             "Description": None
    #         },
    #         "CreditCardData": {
    #             "NameOnCard": self.name_on_card,
    #             "CreditCardNumber": self.credit_card_number,
    #             "ExpirationDate": self.expiration_date,
    #             "CVV": self.cvv
    #         },
    #         "Devices": [
    #             {
    #                 "Name": "TestDevice",
    #                 "Quantity": 2
    #             }
    #         ],
    #         "BeneficialOwnerData": {
    #             "OwnerCount": "1",
    #             "Owners": [
    #                 {
    #                     "FirstName": self.name,
    #                     "LastName": self.last_name,
    #                     "SSN": self.social_security_number,
    #                     "DateOfBirth": "01-01-1981",
    #                     "Email": self.user_id.login,
    #                     "Address": self.address,
    #                     "City": self.city,
    #                     "State": self.state,
    #                     "Zip": self.zip,
    #                     "Country": self.country,
    #                     "Title": "CEO",
    #                     "Percentage": "100"
    #                 }
    #             ]
    #         }
    #     })
    #
    #     headers = {
    #         'Authorization': 'Basic ' + base64_certStr,
    #         'Content-Type': 'application/json'
    #     }
    #     result = ''
    #
    #     response = requests.request("PUT", url, headers=headers, data=payload)
    #     rep = response.__dict__.get('_content')
    #     result = json.loads(rep.decode('utf-8'))
    #
    #     status = result.get('Status')
    #     if status != '00':
    #         error_id = self.env['propay.error.codes'].sudo().search(
    #             [('propay_status_code', '=', int(status))], limit=1)
    #         raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
    #                                          error_id.propay_notes if error_id.propay_notes else '')))
    #     else:
    #         user = self.user_id
    #         user.is_merchant = True
    #         user.partner_id.is_merchant = True
    #         account_number = str(result.get('AccountNumber'))
    #         user.account_number = account_number
    #         merchant_password = result.get('Password')
    #
    #         user.merchant_password = merchant_password
    #
    #         # saving bank account details
    #         user.partner_id.account_country_code = user.encrypt_data(self.account_country_code)
    #         user.partner_id.bank_account_number = user.encrypt_data(self.bank_account_number)
    #         user.partner_id.routing_number = user.encrypt_data(self.routing_number)
    #         user.partner_id.account_ownership_type = user.encrypt_data(self.account_ownership_type)
    #         user.partner_id.bank_name = user.encrypt_data(self.bank_name)
    #         user.partner_id.account_type = user.encrypt_data(self.account_type)
    #
    #         # saving account details
    #         user.partner_id.propay_apartment_number = str(self.apartment_number)
    #         user.partner_id.propay_address = str(self.address)
    #         user.partner_id.propay_city = self.city
    #         user.partner_id.propay_state = self.state
    #         user.partner_id.propay_country = self.country
    #         user.partner_id.propay_zip = self.zip
    #
    #         user.partner_id.first_name = self.name
    #         user.partner_id.last_name = self.last_name
    #         user.partner_id.initial = self.initial
    #         user.partner_id.even_phone = self.even_phone
    #         user.partner_id.day_phone = self.day_phone

