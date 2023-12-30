from odoo import fields, models, api, _
import requests
import base64
import xml.dom.minidom
from lxml import etree
from datetime import datetime

from odoo.exceptions import UserError


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


class MerchantAccountAddress(models.TransientModel):
    _name = 'propay.account.address'
    _description = 'address'

    apartment_number = fields.Char('Apartment Number')
    address = fields.Char('Address')
    city = fields.Char('City')
    state = fields.Char('State')
    country = fields.Char('Country')
    zip = fields.Char('Zip')

    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    initial = fields.Char('Initial')
    day_phone = fields.Char('Day Phone')
    even_phone = fields.Char('Even Phone')
    user_id = fields.Many2one('res.users')
    email = fields.Char('Email')

    def change_merchant_account(self):
        """change address"""

        class_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Class String for ProPay')

        cert_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        x509_cert = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.x509_cert')
        sample_string_bytes = x509_cert.encode("ascii")
        base64_bytes = base64.b64encode(sample_string_bytes)

        if not cert_str and not term_id and not x509_cert:
            raise UserError('Add authentication credentials for ProPay')

        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n" \
                  "<certStr>{certStr}</certStr>\n" \
                  "<termid>{termid}</termid>\n" \
                  "<class>partner</class>\n" \
                  "<XMLTrans>\n" \
                  "<transType>42</transType>" \
                  "\n<accountNum>{accountNum}</accountNum>" \
                  "\n<dayPhone>{dayPhone}</dayPhone>\n" \
                  "<evenPhone>{evenPhone}</evenPhone>\n" \
                  "<firstName>{firstName}</firstName>\n" \
                  "<lastName>{lastName}</lastName>\n" \
                  "<mInitial>{mInitial}</mInitial>\n" \
                  "<sourceEmail>{sourceEmail}</sourceEmail>\n" \
                  "</XMLTrans>\n" \
                  "</XMLRequest>\n".format(class_str, device_str, certStr=cert_str, termid=term_id,
                                           accountNum=self.user_id.account_number, dayPhone=self.day_phone,
                                           evenPhone=self.even_phone, firstName=self.first_name,
                                           lastName=self.last_name, mInitial=self.initial, sourceEmail=self.email)
        headers = {
            'Content-Type': 'application/xml',
            'X509Certificate': x509_cert
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        # Convert xml to dict
        xml_data = xml.dom.minidom.parseString(response.content)
        xml_string = xml_data.toprettyxml()
        tree = etree.fromstring(xml_string)
        dic = dictlist(tree)
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        status = ''
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
        if status == '00':
            self.user_id.partner_id.first_name = self.first_name
            self.user_id.partner_id.last_name = self.last_name
            self.user_id.partner_id.initial = self.initial
            self.user_id.partner_id.even_phone = self.even_phone
            self.user_id.partner_id.day_phone = self.day_phone
            self.user_id.partner_id.email = self.email
        else:
            error_id = self.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                             error_id.propay_notes if error_id.propay_notes else '')))


class MerchantBankAccount(models.TransientModel):
    _name = 'propay.bank.account'
    _description = 'bank account'

    account_country_code = fields.Char('Account Country Code')
    bank_account_number = fields.Char('Bank Account Number')
    routing_number = fields.Char('Routing Number')
    account_ownership_type = fields.Char('Account Ownership Type')
    bank_name = fields.Char('Bank Name')
    account_type = fields.Char('Account Type')
    user_id = fields.Many2one('res.users')

    def check_bank_account(self):
        class_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Device String for ProPay')

        cert_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        x509_cert = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.x509_cert')
        if not cert_str and not term_id and not x509_cert:
            raise UserError('Add authentication credentials for ProPay')

        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
        certificate = "MIICpDCCAYygAwIBAgIIXoPPPLNmk3UwDQYJKoZIhvcNAQENBQAwETEPMA0GA1UEAwwGUFJPUEFZMB4XDTIyMDUwNTAwMDAwMFoXDTMyMDUwNTAwMDAwMFowEzERMA8GA1UEAwwIMTI3LjAuMDEwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCoJcGQN4oDsrk0bm4C4lLr/IYGLfMXcEKjAYOwsnFxq96gJjEcWI/2+nvn9pHyaNoHQlZ8fM7fbzlSVpEsAE0/u1E48imsAfU9Q7xaS+sQJ+p7inEG3o5V1TnhTp+OJJ3nc7GyI+tCPfhwbOqQxTKfIznsV3cRXxMFOepD/02/a4ZvbepRhQudbB8+6VdeqNsjpoZMTxI8Z6RD28iaFmRC/+ZcEg0/5aqgJJDuh2O7V7A7XkJsIObrlw0MwCMjPWr+LrVIaMApdP8Z7qzBLR99oKAR06VjVrkcqAA8Wq+Se4+RLXGdS1AXePBQbXS0BggYdnHbSqGWsH7L3cdvVLcbAgMBAAEwDQYJKoZIhvcNAQENBQADggEBAAa0Z0j3zsJSCnSGt8iUFgFkMsX/F6/7zvCpKQAHN2qBI8K5EEsz9EtBl00esetmsuNbnQjjSe2f86T/ZqimlZ0MIEA8CR0vxWaN9tXC107ZsPBFFq30RMlzLIF0HNVMijjp+RRVJ25On/djkGGp6GBl3Xp+3CbTuwvKj0576nlf9sfp4ZDT2qVzpk3nSUoJsDke2+KJljADV9LDfSUX8bPaL3533ObCMIUxaNiojZs2ZEkGFU9EpY7NHWJjXWAY1f4F1A+phEJyo63CTwkjhhUExy4Al1NFWCAAvYIq3O8yiSfT/KCJxXEZz5eUsTwuX8XsQR4tYtq4iEibVNp3/4E="

        payload = "<?xml version='1.0'?>\n<!DOCTYPE Request.dtd>\n<XMLRequest>\n<certStr>{certStr}</certStr>\n<termid>{termid}</termid>" \
                  "\n<X509Certificate>{X509Certificate}</X509Certificate>\n" \
                  "<class>partner</class>\n<XMLTrans>" \
                  "\n<transType>42</transType>" \
                  "\n<accountNum>{accountNum}</accountNum>\n" \
                  "<AccountCountryCode>{AccountCountryCode}</AccountCountryCode>" \
                  "\n<accountType>{accountType}</accountType>\n" \
                  "<AccountNumber>{AccountNumber}</AccountNumber>" \
                  "\n<BankeName>{BankeName}</BankeName>" \
                  "\n<RoutingNumber>{RoutingNumber}</RoutingNumber>\n" \
                  "<AccountOwnershipType></AccountOwnershipType>\n</XMLTrans>\n</XMLRequest>"\
            .format(class_str, device_str, certStr=cert_str, termid=term_id, X509Certificate=x509_cert,
                    accountNum=self.user_id.account_number, AccountCountryCode=self.account_country_code,
                    accountType=self.account_type, AccountNumber=self.bank_account_number,
                    BankeName=self.bank_name, RoutingNumber=self.routing_number)
        headers = {
            'X509Certificate': x509_cert,
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        # Convert xml to dict
        xml_data = xml.dom.minidom.parseString(response.content)
        xml_string = xml_data.toprettyxml()
        tree = etree.fromstring(xml_string)
        dic = dictlist(tree)
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        status = ''
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
        if status == '00':
            self.user_id.partner_id.account_country_code = self.user_id.encrypt_data(self.account_country_code)
            self.user_id.partner_id.bank_account_number = self.user_id.encrypt_data(self.bank_account_number)
            self.user_id.partner_id.routing_number = self.user_id.encrypt_data(self.routing_number)
            self.user_id.partner_id.account_ownership_type = self.user_id.encrypt_data(self.account_ownership_type)
            self.user_id.partner_id.bank_name = self.user_id.encrypt_data(self.bank_name)
            self.user_id.partner_id.account_type = self.user_id.encrypt_data(self.account_type)
        else:
            error_id = self.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                             error_id.propay_notes if error_id.propay_notes else '')))


class BeneficialData(models.TransientModel):
    _name = 'beneficial.data'
    _description = 'beneficial data'

    user_id = fields.Many2one('res.users')
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    title = fields.Char('Title')
    percentage = fields.Char('Percentage')
    ssn = fields.Char('SSN')
    address = fields.Char('Address')
    country_id = fields.Char('Country')
    state_id = fields.Char('State')
    city = fields.Char('City')
    zip = fields.Char('Zip')
    email = fields.Char('Email')
    date_of_birth = fields.Date('Date Of Birth')

    def add_beneficial_data(self):
        class_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Device String for ProPay')

        cert_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        if not self.date_of_birth:
            raise UserError('Add Date of Birth')

        if not cert_str and not term_id:
            raise UserError('Add authentication credentials for ProPay')

        if self.date_of_birth:
            date = datetime.strptime(str(self.date_of_birth), '%Y-%M-%d')
            date_of_birth = date.strftime('%d-%M-%Y')



        url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n" \
                  "<certStr>{certStr}</certStr>\n" \
                  "<termid>{termid}</termid>\n " \
                  "<class>partner</class>\n " \
                  "<XMLTrans>\n " \
                  "<transType>44</transType>\n " \
                  "<accountNum>{accountNum}</accountNum>\n " \
                  "<BeneficialOwnerData>\n " \
                  "<Owners>\n " \
                  "<Owner>\n " \
                  "<FirstName>{FirstName}</FirstName>\n " \
                  "<LastName>{LastName}</LastName>\n " \
                  "<Title>{Title}</Title>\n " \
                  "<Address>{Address}</Address>\n " \
                  "<Percentage>{Percentage}</Percentage>\n " \
                  "<SSN>{SSN}</SSN>\n " \
                  "<Country>{Country}</Country>\n " \
                  "<State>{State}</State>\n " \
                  "<City>{City}</City>\n " \
                  "<Zip>{Zip}</Zip>\n " \
                  "<Email>{Email}</Email>\n " \
                  "<DateOfBirth>{DateOfBirth}</DateOfBirth>\n " \
                  "</Owner>\n " \
                  "</Owners>\n " \
                  "</BeneficialOwnerData>\n " \
                  "</XMLTrans>\n" \
                  "</XMLRequest>".format(class_str, device_str, certStr=cert_str, termid=term_id,
                                         accountNum=self.user_id.account_number, FirstName=self.first_name,
                                         LastName=self.last_name, Title=self.title, Address=self.address,
                                         Percentage=self.percentage, SSN=self.ssn, Country=self.country_id,
                                         State=self.state_id, City=self.city, Zip=self.zip, Email=self.email,
                                         DateOfBirth=date_of_birth)
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
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
                break

        if status != '00':
            error_id = self.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                             error_id.propay_notes if error_id.propay_notes else '')))
