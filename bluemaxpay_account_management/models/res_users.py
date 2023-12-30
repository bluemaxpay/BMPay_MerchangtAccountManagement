import xml

from werkzeug import urls

from odoo import fields, models, api, _
import json
from cryptography.fernet import Fernet
from lxml import etree
import xml.dom.minidom
import logging
import pprint

import base64
from odoo.exceptions import UserError
from odoo.http import request
import requests

_logger = logging.getLogger(__name__)

key = Fernet.generate_key()


def dictlist(node):
    res = {}
    res[node.tag] = []
    myxmltodict(node, res[node.tag])
    reply = {}
    reply[node.tag] = res[node.tag]
    return reply


def myxmltodict(node, res):
    rep = {}
    if len(node):
        for n in list(node):
            rep[node.tag] = []
            value = myxmltodict(n, rep[node.tag])
            if len(n):
                value = rep[node.tag]
                res.append({n.tag: value})
            else:
                res.append(rep[node.tag][0])
    else:
        value = {}
        value = node.text
        res.append((node.tag, value))
    return


class ResUsersMerchant(models.Model):
    _inherit = 'res.users'

    account_number = fields.Char('Account Number', readonly=True)
    merchant_password = fields.Char('Password', readonly=True)
    beneficial_owner_count = fields.Integer('Beneficial Owner Count')
    is_merchant = fields.Boolean('Is Merchant')
    merchant_active = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')], readonly=False)
    create_merchant_wizard_id = fields.Many2one('create.merchant')
    propay_public_key = fields.Char()
    propay_secret_key = fields.Char()

    @api.onchange('is_merchant')
    def _onchange_is_merchant(self):
        for rec in self:
            rec.partner_id.is_merchant = rec.is_merchant

    def encrypt_data(self, message):
        message_byte = message.encode('ascii')
        message_base64_bytes = base64.b64encode(message_byte)
        encode_message = message_base64_bytes.decode('ascii')
        return encode_message

    def decrypt_data(self, message):
        if not message:
            return message
        message_base64_bytes = base64.b64decode(message)
        decode_message = message_base64_bytes.decode('ascii')
        return decode_message

    def send_merchant_account_form(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')
        Urls = urls.url_join(base_url,
                             '/propay/merchant/creation/?id=' + str(self.id))

        mail_content = _('Hi %s,<br>'
                         'Create a Merchant Account'
                         '<div style = "text-align: center; margin-top: 16px;"><a href = "%s"'
                         'style = "padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; '
                         'border-color:#875A7B;text-decoration: none; display: inline-block; '
                         'margin-bottom: 0px; font-weight: 400;text-align: center; vertical-align: middle; '
                         'cursor: pointer; white-space: nowrap; background-image: none; '
                         'background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px;">'
                         'View %s</a></div>'
                         ) % \
                       (self.login, Urls, self.login)
        email_to = self.partner_id

        main_content = {
            'subject': _('Create Merchant account'),
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': email_to.email
        }
        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.mail_message_id.body = mail_content
        mail_id.send()
        pass

    def single_sign_on_token(self):
        url = "https://icanhazip.com"
        payload = {}
        headers = {}
        response_ = requests.request("POST", url, headers=headers, data=payload)
        _logger.info("request response:\n%s", pprint.pformat(response_.text))
        ip = request.httprequest.environ.get('HTTP_X_REAL_IP', '127.0.0.1')
        _logger.info(
            "===========================================================")
        _logger.info(request.httprequest.__dict__)
        _logger.info(
            "===========================================================")
        response = requests.get(
            'https://api64.ipify.org?format=json').json()
        _logger.info(response)
        ip_address = ip
        response = requests.get(
            f'https://ipapi.co/{ip_address}/json/').json()
        location_data = {
            "ip_address": ip_address,
            "city": response.get("city"),
            "region": response.get("region"),
            "country": response.get("country_name")
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Account Management',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'single.sign.on',
            'context': {
                'default_user_id': self.id,
                'default_ip_address': response_.text.strip(),
                'default_ip_subnet_mask': response_.text.strip()
            }
        }

    def remove_affiliation(self):
        # remove affiliation of propay account
        class_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Device String for ProPay')


        cert_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id')
        if not cert_str and not term_id:
            raise UserError('Add authentication credentials for ProPay')

        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n " \
                  "<certStr>{certStr}</certStr>\n " \
                  "<termid>{termid}</termid>\n " \
                  "<class>partner</class>\n " \
                  "<XMLTrans>\n " \
                  "<transType>41</transType>\n " \
                  "<accountNum>{accountNum}</accountNum>\n " \
                  "<AccountType>Checking</AccountType>\n" \
                  "</XMLTrans>\n" \
                  "</XMLRequest>".format(class_str, device_str, certStr=cert_str, termid=term_id, accountNum=self.account_number)
        headers = {
            'Content-Type': 'application/xml',
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        # Convert xml to dict
        xml_data = xml.dom.minidom.parseString(response.content)
        xml_string = xml_data.toprettyxml()
        tree = etree.fromstring(xml_string)
        dic = dictlist(tree)
        status = ''
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        # status = XMLTrans[1]['status']
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
                break
        if status != '00':
            raise UserError(
                _('The Request is Failed. Response status as %s') % status)

    def change_merchant_password(self):
        class_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Device String for ProPay')

        cert_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id')
        if not cert_str and not term_id:
            raise UserError('Add authentication credentials for ProPay')

        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n" \
                  " <certStr>{certStr}</certStr>\n " \
                  "<termid>{termid}</termid>\n    " \
                  "<class>partner</class>\n    " \
                  "<XMLTrans>\n        " \
                  "<transType>32</transType>\n        " \
                  "<accountNum>{accountNum}</accountNum>\n    " \
                  "</XMLTrans>\n" \
                  "</XMLRequest>\n".format(class_str, device_str, certStr=cert_str, termid=term_id,
                                           accountNum=self.account_number)
        headers = {
            'Content-Type': 'application/xml',
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        # Convert xml to dict
        xml_data = xml.dom.minidom.parseString(response.content)
        xml_string = xml_data.toprettyxml()
        tree = etree.fromstring(xml_string)
        dic = dictlist(tree)
        status = ''
        password = ''
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        # status = XMLTrans[1]['status']
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
            elif trans[0] == 'password':
                password = trans[1]

        if status == '00':
            self.merchant_password = password
        else:
            raise UserError('You Cant Change the Password')

    def update_beneficial_owner_count(self):
        class_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Device String for ProPay')

        cert_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id')
        if not cert_str and not term_id:
            raise UserError('Add authentication credentials for ProPay')

        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n" \
                  "<sourceip></sourceip>\n" \
                  "<certStr>{certStr}</certStr>\n" \
                  "<termid>{termid}</termid>\n" \
                  "<XMLTrans>\n" \
                  "<transType>211</transType>\n" \
                  "<accountNum>{accountNum}</accountNum>\n" \
                  "<BeneficialOwnerData>\n" \
                  "<OwnerCount>{OwnerCount}</OwnerCount>\n" \
                  "</BeneficialOwnerData>\n" \
                  "</XMLTrans>\n" \
                  "</XMLRequest>"\
            .format(class_str, device_str, certStr=cert_str, termid=term_id, accountNum=self.account_number,
                    OwnerCount=self.beneficial_owner_count)

        headers = {
            'Content-Type': 'application/xml'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        # Convert xml to dict
        xml_data = xml.dom.minidom.parseString(response.content)
        xml_string = xml_data.toprettyxml()
        tree = etree.fromstring(xml_string)
        dic = dictlist(tree)
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        # status = XMLTrans[1]['status']
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
                break

        if status == '159':
            _logger.error(_('Please change the Beneficial Owner Count'))
            raise UserError(_('Please change the Beneficial Owner Count'))
        elif status != '00':
            _logger.error(_('The Request is Failed. Response status as %s') % status)
            raise UserError(
                _('The Request is Failed. Response status as %s') % status)

    def action_view_merchant(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Merchant Account',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'create.merchant',
            'res_id': self.create_merchant_wizard_id.id,
        }

    def create_merchant(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Merchant Account',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'create.merchant',
            'context': {
                'default_user_id': self.id,
            }
        }

        cert_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id')
        if cert_str:
            if term_id:
                certStr = cert_str + ':' + term_id
            else:
                raise UserError('Add authentication credentials for ProPay')

        certStr_bytes = certStr.encode('ascii')
        certStr_base64_bytes = base64.b64encode(certStr_bytes)
        base64_certStr = certStr_base64_bytes.decode('ascii')

        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_signup_url')
        termid = '0787ae'
        ascii_values = []
        for character in certStr:
            ascii_values.append(ord(character))
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'web.base.url')

        payload = json.dumps({
            "PersonalData": {
                "FirstName": self.name,
                # "MiddleInitial": "X",
                "LastName": self.name,
                "DateOfBirth": "01-01-1992",
                "SocialSecurityNumber": "987654321",
                "SourceEmail": self.partner_id.email,
                "PhoneInformation": {
                    "DayPhone": self.partner_id.phone,
                    "EveningPhone": self.partner_id.phone
                },
                "NotificationEmail": "democompanys71234@gmail.com",
                "TimeZone": "UTC"
            },
            "SignupAccountData": {
                "CurrencyCode": "USD",
                "Tier": "Test"
            },
            "BusinessData": {
                "BusinessLegalName": "Merchantile Parent, Inc.",
                "DoingBusinessAs": "Merchantile ABC",
                "EIN": "121232343",
                # "MerchantCategoryCode": "5999",
                "WebsiteURL": base_url,
                "BusinessDescription": "Accounting Services",
                "MonthlyBankCardVolume": 10000,
                "AverageTicket": 100,
                "HighestTicket": 250
            },
            "Address": {
                "ApartmentNumber": "1",
                "Address1": self.partner_id.street,
                # "Address2": "Suite 200",
                "City": self.partner_id.city,
                "State": self.partner_id.state_id.code,
                # "Country": self.partner_id.country_id.code,
                "Zip": self.partner_id.zip
            },
            "BusinessAddress": {
                "ApartmentNumber": "200",
                "Address1": self.partner_id.street,
                # "Address2": "SW",
                "City": self.partner_id.city,
                "State": self.partner_id.state_id.code,
                # "Country": self.partner_id.country_id.code,
                "Country": 'USA',
                "Zip": self.partner_id.zip
            },
            "BankAccount": {
                "AccountCountryCode": "USA",
                "BankAccountNumber": "123456789",
                "RoutingNumber": "011306829",
                "AccountOwnershipType": "Business",
                "BankName": "MERCHANTILE BANK UT",
                "AccountType": "Checking",
                "AccountName": None,
                "Description": None
            },
            "CreditCardData": {
                "NameOnCard": "First X Last",
                "CreditCardNumber": "4111111111111111",
                "ExpirationDate": "0127",
                "CVV": "999"
            },
            "Devices": [
                {
                    "Name": "TestDevice",
                    "Quantity": 1
                }
            ],
            "BeneficialOwnerData": {
                "OwnerCount": "1",
                "Owners": [{
                    "FirstName": "First1",
                    "LastName": "Last1",
                    "SSN": "123456789",
                    "DateOfBirth": "01-01-1981",
                    "Email": "test1@qamail.com",
                    "Address": "Address",
                    "City": "Lehi",
                    "State": "UT",
                    "Zip": "84010",
                    "Country": "USA",
                    "Title": "CEO",
                    "Percentage": "100"
                }]
            },
        })
        headers = {
            'Authorization': 'Basic ' + base64_certStr,
            'Content-Type': 'application/json'
        }

        response = requests.request("PUT", url, headers=headers, data=payload)

        rep = response.__dict__.get('_content')
        result = json.loads(rep.decode('utf-8'))

        account_number = result.get('AccountNumber')
        self.account_number = account_number
        merchant_password = result.get('Password')
        self.merchant_password = merchant_password
        # account

    def upload_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Document Upload Account',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'document.upload',
            'context': {
                'default_account_number': self.account_number,
            }
        }

    def ach_transaction(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'ACH Transaction',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'ach.transaction',
            'context': {
                'default_user_id': self.id,
            }
        }

    def merchant_account_edit(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Merchant Account',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'merchant.account.management',
            'context': {
                'default_user_id': self.id,
            }
        }

    def master_card_pin_mailer(self):
        class_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Device String for ProPay')

        cert_str = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id')
        if not cert_str and not term_id:
            raise UserError('Add authentication credentials for ProPay')

        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n " \
                  "<certStr>{certStr}</certStr>\n " \
                  "<termid>{termid}</termid>\n " \
                  "<class>partner</class>\n " \
                  "<XMLTrans>\n " \
                  "<transType>30</transType>\n " \
                  "<accountNum>{accountNum}</accountNum>\n " \
                  "</XMLTrans>\n" \
                  "</XMLRequest>".format(class_str, device_str, certStr=cert_str, termid=term_id, accountNum=self.account_number)
        headers = {
            'Content-Type': 'application/xml',
            'Cookie': 'ASP.NET_SessionId=bhky2i50wv5cqs2myl0vn2ho; sessionValidation=ba9d8b7f-934f-4018-8120-fb2ed13c124c'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        # Convert xml to dict
        xml_data = xml.dom.minidom.parseString(response.content)
        xml_string = xml_data.toprettyxml()
        tree = etree.fromstring(xml_string)
        dic = dictlist(tree)
        status = ''
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]

    # def action_sso_management(self):
    #     self.ensure_one()
    #     url = "https://api.ipify.org?format=json"
    #     response = requests.request("GET", url)
    #     if response.status_code == 200:
    #         response = response.json()
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'SSO Management',
    #             'view_mode': 'form',
    #             'target': 'new',
    #             'res_model': 'single.sign.on',
    #             'context': {
    #                 'default_user_id': self.id,
    #                 'default_ip_address': response.get('ip'),
    #             }
    #         }
