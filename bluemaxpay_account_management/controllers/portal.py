import os
from odoo import _
import requests
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import route
import xml
import base64
from lxml import etree
import xml.dom.minidom
import logging
import pprint

from odoo.http import request

_logger = logging.getLogger(__name__)
from globalpayments.api import ServicesConfig, ServicesContainer
from globalpayments.api.entities import Address
from globalpayments.api.payment_methods import CreditCardData
from globalpayments.api.entities.exceptions import (ApiException)


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


class ProPaySignUpAccount(CustomerPortal):

    @route(['/my/merchant/account/user/token'], type='http', auth='user', website=True)
    def my_merchant_account_user_token(self, **post):
        user = request.env.user
        secret_api_key = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.secret_api_key')
        developer_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.developer_id')
        version_number = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.version_number')
        if not secret_api_key and not developer_id and not version_number:
            secret_api_key = ''
            developer_id = ''
            version_number = ''
        config = ServicesConfig()
        config.secret_api_key = secret_api_key
        config.service_url = 'https://cert.api2.heartlandportico.com'
        config.developer_id = developer_id
        config.version_number = version_number
        ServicesContainer.configure(config)
        if post.get('number') and post.get('exp_month') and post.get('exp_year') and post.get('cvv') and post.get(
                'name'):
            card = CreditCardData()
            card.number = post.get('number')
            card.exp_month = post.get('exp_month')
            card.exp_year = post.get('exp_year')
            card.cvn = post.get('cvv')
            card.card_holder_name = post.get('name')
            address = Address()
            address.address_type = 'Billing'
            address.postal_code = user.partner_id.zip
            address.postal_code = user.partner_id.zip
            address.country = user.partner_id.country_id.name
            address.state = user.partner_id.state_id.name
            address.city = user.partner_id.city
            address.street_address_1 = user.partner_id.street
            address.street_address_1 = user.partner_id.street2
            try:
                response = card.verify() \
                    .with_address(address) \
                    .with_request_multi_use_token(True) \
                    .execute()
                if response.response_code != '00':
                    request.render("bluemaxpay_account_management.my_merchant_account_user_token", {
                        'number': post.get('number'),
                        'exp_month': post.get('exp_month'),
                        'exp_year': post.get('exp_year'),
                        'cvv': post.get('cvv'),
                        'name': post.get('name'),
                        'error': response.avs_response_message,
                        'create_token': 'create_token',
                        'bluemaxpay_crumb': 'new_token'
                    })
                else:
                    token = request.env['zillo.token'].sudo().create({
                        'partner_id': user.partner_id.id,
                        'name': post.get('name'),
                        'token': response.token
                    })
                    return request.redirect('/my/merchant/account/user/created_tokens')
            except ApiException as e:
                request.render(
                    "bluemaxpay_account_management.my_merchant_account_user_token", {
                        'error': e,
                        'bluemaxpay_crumb': 'new_token'
                    })
        else:
            return request.render("bluemaxpay_account_management.my_merchant_account_user_token", {
                'bluemaxpay_crumb': 'new_token'
            })

    @route(['/my/merchant/account/management'], type='http', auth='user', website=True)
    def my_merchant_account_management(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_account_management", {
            'bluemaxpay_crumb': 'z_management'
        })

    @route(['/my/merchant/account/api_keys'], type='http', auth='user', website=True)
    def my_merchant_account_api_key(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_account_api_key")

    @route(['/my/merchant/account/user/created_tokens'], type='http', auth='user', website=True)
    def my_merchant_account_created_tokens(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_account_user_created_tokens", {
            'bluemaxpay_crumb': 'created_tokens'
        })

    @route(['/my/merchant/account/password'], type='http', auth='user', website=True)
    def my_merchant_account_password(self, **post):
        class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            class_str = ''

        device_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            device_str = ''
        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')

        if not cert_str and not term_id:
            cert_str = ''
            term_id = ''

        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
        user = request.env.user

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
                  "</XMLRequest>\n".format(class_str, device_str, certStr=cert_str,
                                           termid=term_id, accountNum=user.account_number)
        headers = {
            'Content-Type': 'application/xml',
        }
        response = requests.request("POST", url, headers=headers, data=payload)
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
            value = {'message': 'Your Bluemaxpay account password was updated',
                     'password': True, 'value': password}
            user.merchant_password = password
        else:
            value = {'message': 'Your Bluemaxpay account password was updated',
                     'password': False}

        return request.render("bluemaxpay_account_management.merchant_account_password", value)

    @route(['/my/merchant/upload/document'], type='http', auth='user', website=True)
    def my_merchant_upload_document(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_upload_document", {
            'bluemaxpay_crumb': 'upload_document'
        })

    @route(['/my/upload/document'], type='http', auth='user', website=True)
    def my_upload_document(self, **post):
        # name = post.get('attachment').filename
        file = post.get('attachment')
        if file:
            file = post.get('attachment')
            files = base64.b64encode(file.read())
        class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            class_str = ''
        device_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            device_str = ''
        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        if not cert_str and not term_id:
            cert_str = ''
            term_id = ''
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
        user = request.env.user
        qcontext = {}
        qcontext_key = post.keys()
        for rec in qcontext_key:
            qcontext[rec] = post.get(rec)
        if not cert_str and not term_id and class_str and device_str:
            return request.render("bluemaxpay_account_management.my_merchant_upload_document", {
                'document_name': post.get('document_name'),
                'document_category': post.get('document_category'),
                'document_type': post.get('document_type'),
                'bluemaxpay_crumb': 'upload_document'
            })
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
        # for document upload
        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n" \
                  "<certStr>{certStr}</certStr>\n" \
                  "<termid>{termid}</termid>\n" \
                  "<class>partner</class>\n" \
                  "<XMLTrans>\n" \
                  "<transType>47</transType>\n" \
                  "<accountNum>{accountNum}</accountNum>\n" \
                  "<DocumentName>{DocumentName}</DocumentName>\n" \
                  "<DocCategory>{DocCategory}</DocCategory>\n" \
                  "<DocType>{DocType}</DocType>\n" \
                  "<Document>{Document}</Document>\n" \
                  "</XMLTrans>\n" \
                  "</XMLRequest>".format(certStr=cert_str, termid=term_id, accountNum=user.account_number,
                                         DocumentName=post.get('document_name'), DocCategory=post.get('document_category'),
                                         DocType=post.get('document_type'), Document=files.decode('ascii'))

        headers = {
            'Content-Type': 'application/xml',
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
        # status = '00'
        if status != '00':
            error_id = request.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            return request.render(
                "bluemaxpay_account_management.my_merchant_upload_document", {
                    'document_name': str(post.get('document_name')),
                    'document_category': str(post.get('document_category')),
                    'document_type': post.get('document_type'),
                    'bluemaxpay_crumb': 'upload_document',
                    'error': _("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                              error_id.propay_notes if error_id.propay_notes else ''))
                })
        if status == '00':
            return request.render('bluemaxpay_account_management.merchant_upload_document')

    @route(['/my/merchant/bank/details'], type='http', auth='user', website=True)
    def my_merchant_bank_details(self, **post):
        user = request.env.user
        account_country_code = ''
        account_ownership_type = ''
        bank_account_number = ''
        routing_number = ''
        bank_name = ''
        account_type = ''
        if user.partner_id.account_country_code:
            account_country_code = user.decrypt_data(user.partner_id.account_country_code)
        if user.partner_id.account_ownership_type:
            account_ownership_type = user.decrypt_data(user.partner_id.account_ownership_type)
        if user.partner_id.bank_account_number:
            bank_account_number = user.decrypt_data(user.partner_id.bank_account_number)
        if user.partner_id.routing_number:
            routing_number = user.decrypt_data(user.partner_id.routing_number)
        if user.partner_id.bank_name:
            bank_name = user.decrypt_data(user.partner_id.bank_name)
        if user.partner_id.account_type:
            account_type = user.decrypt_data(user.partner_id.account_type)

        return request.render("bluemaxpay_account_management.my_merchant_bank_details", {
            'account_country_code': account_country_code,
            'account_ownership_type': account_ownership_type,
            'bank_account_number': bank_account_number,
            'routing_number': routing_number,
            'bank_name': bank_name,
            'account_type': account_type,
            'bluemaxpay_crumb': 'bank_details'
        })

    @route(['/edit/bank/details'], type='http', auth='user', website=True)
    def my_merchant_edit_bank_details(self, **post):
        user = request.env.user
        class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            class_str = ''

        device_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            device_str = ''

        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        x509_cert = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.x509_cert')
        if not cert_str and not term_id and not x509_cert:
            cert_str = ''
            term_id = ''
            x509_cert = ''
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

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
                  "<AccountOwnershipType>{AccountOwnershipType}</AccountOwnershipType>\n</XMLTrans>\n</XMLRequest>"\
            .format(class_str, device_str, certStr=cert_str, termid=term_id, X509Certificate=x509_cert,
                    accountNum=user.account_number, AccountCountryCode=post.get('account_country_code'),
                    accountType=post.get('account_type'), AccountNumber=post.get('bank_account_number'),
                    BankeName=post.get('bank_name'), RoutingNumber=post.get('routing_number'),
                    AccountOwnershipType=post.get('account_ownership_type'))
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
            user.partner_id.account_country_code = user.encrypt_data(
                post.get('account_country_code'))
            user.partner_id.bank_account_number = user.encrypt_data(
                post.get('bank_account_number'))
            user.partner_id.routing_number = user.encrypt_data(
                post.get('routing_number'))
            user.partner_id.account_ownership_type = user.encrypt_data(
                post.get('account_ownership_type'))
            user.partner_id.bank_name = user.encrypt_data(
                post.get('bank_name'))
            user.partner_id.account_type = user.encrypt_data(
                post.get('account_type'))
            return request.render('bluemaxpay_account_management.merchant_bank_details')
        else:
            error_id = request.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            return request.render("bluemaxpay_account_management.my_merchant_bank_details", {
                'account_country_code': post.get('account_country_code'),
                'account_ownership_type': post.get('account_ownership_type'),
                'bank_account_number': post.get('bank_account_number'),
                'routing_number': post.get('routing_number'),
                'bank_name': post.get('routing_number'),
                'account_type': post.get('account_type'),
                'bluemaxpay_crumb': 'bank_details',
                'error': _("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                          error_id.propay_notes if error_id.propay_notes else ''))
            })

    @route(['/my/merchant/edit/address'], type='http', auth='user', website=True)
    def my_merchant_address_details(self, **post):
        user = request.env.user
        return request.render("bluemaxpay_account_management.my_merchant_address_details", {
            'first_name': user.partner_id.first_name,
            'last_name': user.partner_id.last_name,
            'initial': user.partner_id.initial,
            'day_phone': user.partner_id.day_phone,
            'even_phone': user.partner_id.even_phone,
            'email': user.partner_id.email,
            'bluemaxpay_crumb': 'address_edit'
        })

    @route(['/merchant/edit/address'], type='http', auth='user', website=True)
    def merchant_address_details(self, **post):
        user = request.env.user
        class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            class_str = ''

        device_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            device_str = ''

        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        x509_cert = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.x509_cert')
        if not cert_str and not term_id and not x509_cert:
            cert_str = ''
            term_id = ''
            x509_cert = ''
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
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
                  "</XMLRequest>\n".format(
                      class_str, device_str, certStr=cert_str, termid=term_id, accountNum=user.account_number,
                      dayPhone=post.get('day_phone'),
                      evenPhone=post.get('even_phone'), firstName=post.get('first_name'), lastName=post.get('last_name'),
                      mInitial=post.get('initial'), sourceEmail=post.get('email'))
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
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
        if status == '00':
            user.partner_id.first_name = post.get('first_name')
            user.partner_id.last_name = post.get('last_name')
            user.partner_id.initial = post.get('initial')
            user.partner_id.even_phone = post.get('even_phone')
            user.partner_id.day_phone = post.get('day_phone')
            user.partner_id.email = post.get('email')
            return request.render('bluemaxpay_account_management.merchant_address_details')
        else:
            error_id = request.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            return request.render(
                "bluemaxpay_account_management.my_merchant_address_details", {
                    'first_name': user.partner_id.first_name,
                    'last_name': user.partner_id.last_name,
                    'initial': user.partner_id.initial,
                    'day_phone': user.partner_id.day_phone,
                    'even_phone': user.partner_id.even_phone,
                    'email': user.partner_id.email,
                    'bluemaxpay_crumb': 'address_edit',
                    'error': _("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                              error_id.propay_notes if error_id.propay_notes else ''))
                })

    @route(['/my/merchant/beneficial/owner/data'], type='http', auth='user', website=True)
    def my_merchant_beneficial_owner_data(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_beneficial_owner_data",
                              {'bluemaxpay_crumb': 'owner_data'})

    @route(['/merchant/beneficial/owner/data'], type='http', auth='user',
           website=True)
    def merchant_beneficial_owner_data(self, **post):
        user = request.env.user
        class_str = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str')
        if not class_str:
            class_str = ''

        device_str = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.device_str')
        if not device_str:
            device_str = ''

        cert_str = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id')
        if not cert_str and not term_id:
            cert_str = ''
            term_id = ''

        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
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
                                         accountNum=user.account_number, FirstName=post.get('first_name'),
                                         LastName=post.get('last_name'), Title=post.get('title'),
                                         Address=post.get('address'), Percentage=post.get('percentage'),
                                         SSN=post.get(''), Country=post.get('country'), State=post.get('state'),
                                         City=post.get('city'), Zip=post.get('zip_code'), Email=post.get('email'),
                                         DateOfBirth=post.get('date_of_birth'))
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
            error_id = request.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            return request.render(
                "bluemaxpay_account_management.my_merchant_beneficial_owner_data", {
                    'first_name': post.get('last_name'),
                    'last_name': post.get('last_name'),
                    'title': post.get('title'),
                    'percentage': post.get('percentage'),
                    'address': post.get('address'),
                    'country': post.get('country'),
                    'state': post.get('state'),
                    'city': post.get('city'),
                    'ssn': post.get('ssn'),
                    'zip_code': post.get('zip_code'),
                    'email': post.get('email'),
                    'bluemaxpay_crumb': 'owner_data',
                    'date_of_birth': post.get('date_of_birth'),
                    'error': _("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                              error_id.propay_notes if error_id.propay_notes else ''))
                })
        else:
            return request.render('bluemaxpay_account_management.merchant_beneficial_owner_data')

    @route(['/my/merchant/ach/transaction/data'], type='http', auth='user', website=True)
    def my_merchant_ach_transaction_data(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_ach_transaction_data", {
            'bluemaxpay_crumb': 'data'
        })

    @route(['/merchant/ach/transaction/data'], type='http', auth='user', website=True)
    def merchant_ach_transaction_data(self, **post):
        user = request.env.user
        class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            class_str = ''

        device_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            device_str = ''

        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        if not term_id and not cert_str:
            term_id = ''
            cert_str = ''
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n " \
                  "<certStr>{certStr}</certStr>\n " \
                  "<termid>{termid}</termid>\n " \
                  "<class>partner</class>\n " \
                  "<XMLTrans>\n " \
                  "<transType>36</transType>\n " \
                  "<amount>{amount}</amount>\n " \
                  "<accountNum>{accountNum}</accountNum>\n " \
                  "<RoutingNumber>{RoutingNumber}</RoutingNumber>\n " \
                  "<AccountNumber>{AccountNumber}</AccountNumber>\n " \
                  "<accountType>{accountType}</accountType>\n " \
                  "<StandardEntryClassCode>{StandardEntryClassCode}</StandardEntryClassCode>\n " \
                  "<accountName>{accountName}</accountName>\n " \
                  "<invNum>{invNum}</invNum>\n " \
                  "</XMLTrans>\n" \
                  "</XMLRequest>".format(class_str, device_str, certStr=cert_str, termid=term_id,
                                         amount=post.get('amount'), accountNum=user.account_number,
                                         RoutingNumber=post.get('routing_number'), AccountNumber=user.account_number,
                                         accountType=post.get('account_type'),
                                         StandardEntryClassCode=post.get('standard_entry_class_code'),
                                         accountName=post.get('account_name'), invNum=post.get('inv_num'))
        headers = {
            'Content-Type': 'application/xml',
            'Cookie': 'ASP.NET_SessionId=t3syihir520r52hbyovggouh; sessionValidation=2c043bb5-0048-476d-adea-10ae8395c774'
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
        if status == '00':
            request.render("bluemaxpay_account_management.merchant_ach_transaction_data")
        else:
            error_id = request.env['propay.error.codes'].sudo().search([('propay_status_code', '=', int(status))],
                                                                       limit=1)
            return request.render(
                "bluemaxpay_account_management.my_merchant_ach_transaction_data", {
                    'routing_number': post.get('routing_number'),
                    'amount': post.get('routing_number'),
                    'bluemaxpay_crumb': 'data',
                    'account_type': post.get('account_type'),
                    'standard_entry_class_code': post.get('standard_entry_class_code'),
                    'account_name': post.get('account_name'),
                    'inv_num': post.get('inv_num'),
                    'error': _("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                              error_id.propay_notes if error_id.propay_notes else ''))
                })

    @route(['/my/merchant/beneficial/owner/count'], type='http', auth='user', website=True)
    def my_merchant_beneficial_owner_count(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_beneficial_owner_count", {
            'bluemaxpay_crumb': 'count'
        })

    @route(['/merchant/beneficial/owner/count'], type='http', auth='user', website=True)
    def merchant_beneficial_owner_count(self, **post):
        user = request.env.user
        number = post.get('count')
        if 5 >= int(number) >= 1:
            class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
            if not class_str:
                class_str = ''
            device_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
            if not device_str:
                device_str = ''
            cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
            term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
            if not cert_str and not term_id:
                cert_str = ''
                term_id = ''
            url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
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
                      "</XMLRequest>".format(class_str, device_str, certStr=cert_str, termid=term_id,
                                             accountNum=user.account_number, OwnerCount=post.get('count'))
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
            if status != '00':
                error_id = request.env['propay.error.codes'].sudo().search(
                    [('propay_status_code', '=', int(status))], limit=1)
                return request.render(
                    "bluemaxpay_account_management.my_merchant_beneficial_owner_count", {
                        'bluemaxpay_crumb': 'count',
                        'error': _("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                                  error_id.propay_notes if error_id.propay_notes else ''))
                    })
            else:
                user.beneficial_owner_count = post.get('count')
                return request.render(
                    "bluemaxpay_account_management.my_merchant_beneficial_owner_count", {
                        'message': 'Updated the beneficial onwership count',
                        'bluemaxpay_crumb': 'count'
                    })
        else:
            return request.render(
                "bluemaxpay_account_management.my_merchant_beneficial_owner_count", {
                    'error': 'Please Change the count value',
                    'bluemaxpay_crumb': 'count'
                })

    @route(['/my/merchant/device/order'], type='http', auth='user', website=True)
    def my_merchant_order_details(self, **post):
        return request.render("bluemaxpay_account_management.my_merchant_order_details", {'bluemaxpay_crumb': 'orders'})

    @route(['/merchant/device/order'], type='http', auth='user', website=True)
    def merchant_order_data(self, **post):
        user = request.env.user
        class_str = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str')
        if not class_str:
            class_str = ''
        device_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            device_str = ''
        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        device = request.env['propay.device'].sudo().search([('id', '=', post.get('device'))])
        if not cert_str and not term_id:
            cert_str = ''
            term_id = ''
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

        payload = "<?xml version='1.0'?>\n" \
                  "<!DOCTYPE Request.dtd>\n" \
                  "<XMLRequest>\n " \
                  "<certStr>{certStr}</certStr>\n " \
                  "<termid>{termid}</termid>\n " \
                  "<class>partner</class>\n " \
                  "<XMLTrans>\n " \
                  "<transType>430</transType>\n " \
                  "<accntNum>{accntNum}</accntNum>\n " \
                  "<shipTo>{shipTo}</shipTo>\n " \
                  "<shipToContact>{shipToContact}</shipToContact>\n " \
                  "<shipToAddress>{shipToAddress}</shipToAddress>\n " \
                  "<shipToAddress2>{shipToAddress2}</shipToAddress2>\n " \
                  "<shipToCity>{shipToCity}</shipToCity>\n " \
                  "<shipToState>{shipToState}</shipToState>\n " \
                  "<shipToZip>{shipToZip}</shipToZip>\n " \
                  "<shipToPhone>{shipToPhone}</shipToPhone>\n " \
                  "<cardholderName>{cardholderName}</cardholderName>\n " \
                  "<CcNum>{CcNum}</CcNum>\n " \
                  "<ExpDate>{ExpDate}</ExpDate>\n " \
                  "<CVV2>{CVV2}</CVV2>\n " \
                  "<billingZip>{billingZip}</billingZip>\n " \
                  "<PostbackUrl>https://apis-sit.globalpay.com/ucp/postback/merchants\n /platform/eyJtY3NfcmF3X2RhdGEiOnsibW1hX2lkIjoiTU1BXzBm\n M TA0ZjYxMTk4ODQ5MDE4ZjI1NWYzNjRlN2M0ZDllIiwicHJvZHVjdC\n I6W10sIm1jc19tZXJjaGFudF9pZCI6Ik1FUl9kODdkOGE1NmI4YzQ0\n ZjVkYWY1YzEw NzExZDkw YzA0M iJ9LCJYLUdQLVZlcnNpb24iOiIyMDIxLTAzLTIyIiwibV9hcHBfaWQiOiJqd0VrTUo4bUNYRVVQNkVXdjUw\n OFc2WU1qNXpQSlNOVyIsInhfZ2xvYmFsX3RyYW5zYWN0aW9uX2lkIj\n oicnJ0LWY5ZGI5OTk3LWI2ZTgtNDUzZS1iNWEyLTlhNmJiNTMxNGJj\n M mY4bDh1In0=</PostbackUrl>\n " \
                  "<PostbackUrl2>https://apis-sit.globalpay.com/ucp/postback/merchants/platform/\n eyJtY3NfcmF3X2RhdGEiOnsibW1hX2lkIjoiTU1BXzBmMTA0ZjYxMTk4ODQ5MDE\n 4ZjI1NWYzNjRlN2M 0ZDllIiwicHJvZHVjdCI6W10sIm1jc19tZXJjaGFudF9pZC\n I6Ik1FUl9kODdkOGE1NmI4YzQ0ZjVkYWY1YzEw NzExZDkwYzA0MiJ9LCJYLUdQL\n VZlcnNpb24iOiIyMDIxLTAzLTIyIiwibV9hcHBfaWQiOiJqd0VrTUo4bUNYRVVQ\n NkVXdjUw OFc2WU1qNXpQSlNOVyIsInhfZ2xvYmFsX3RyYW5zYWN0aW9uX2lkIjo\n icnJ0LWY5ZGI5OTk3LWI2ZTgtNDUzZS1iNWEyLTlhNmJiNTMxNGJjMmY4b\n Dh1In0=</PostbackUrl2>\n " \
                  "<Devices>\n " \
                  "<Device>\n" \
                  "<Name>{Name}</Name>\n " \
                  "<Quantity>{Quantity}</Quantity>\n " \
                  "<Attributes>\n " \
                  "<Item Name=\"Heartland.AMD.OfficeKey\" Value=\"45\"/>\n " \
                  "</Attributes>\n " \
                  "</Device>\n " \
                  "</Devices>\n" \
                  "</XMLTrans>\n" \
                  "</XMLRequest>".format(
                      class_str, device_str, certStr=cert_str, termid=term_id, accntNum=user.account_number,
                      shipTo=post.get('ship_to'), shipToContact=post.get('ship_to_contact'),
                      shipToAddress=post.get('ship_to_address'), shipToAddress2=post.get('ship_to_address2'),
                      shipToCity=post.get('ship_to_city'),
                      shipToState=post.get('ship_to_state'),
                      shipToZip=post.get('ship_to_zip'), shipToPhone=post.get('ship_to_phone'),
                      cardholderName=post.get('cardholder_name'),
                      CcNum=post.get('cc_num'),
                      ExpDate=post.get('exp_date'),
                      CVV2=post.get('CVV2'), billingZip=post.get('billing_zip'),
                      Name=device.name, Quantity=post.get('qty'))
        headers = {
            'Content-Type': 'application/xml',
        }
        response = requests.request("GET", url, headers=headers, data=payload)
        xml_data = xml.dom.minidom.parseString(
            response.content)  # Prepare xml DOM Structure
        xml_string = xml_data.toprettyxml()  # it is used to print the xml in standard format
        tree = etree.fromstring(xml_string)  # Tree to string
        dic = dictlist(tree)  # Dictionary List
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        status = ''
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
                break
        if status != '00':
            # raise UserError(_('The Request is Failed. Response status as %s') % status)
            error_id = request.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            values = {
                'ship_to': post.get('ship_to'),
                'ship_to_contact': post.get('ship_to_contact'),
                'ship_to_address': post.get('ship_to_address'),
                'ship_to_address2': post.get('ship_to_address2'),
                'ship_to_city': post.get('ship_to_city'),
                'ship_to_state': post.get('ship_to_state'),
                'ship_to_zip': post.get('ship_to_zip'),
                'ship_to_phone': post.get('ship_to_phone'),
                'cardholder_name': post.get('cardholder_name'),
                'cc_num': post.get('cc_num'),
                'exp_date': post.get('exp_date'),
                'CVV2': post.get('CVV2'),
                'billing_zip': post.get('billing_zip'),
                'device_name': post.get('device_name'),
                'bluemaxpay_crumb': 'orders',
                'qty': post.get('qty'),
                'error': _("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                          error_id.propay_notes if error_id.propay_notes else ''))

            }
            return request.render('bluemaxpay_account_management.my_merchant_order_details', values)
        else:
            return request.render('bluemaxpay_account_management')

    @route(['/my/merchant/single_sign_on'], type='http', auth='user', website=True)
    def my_merchant_single_sign_on(self, **post):
        # 1
        # nics = psutil.net_if_addrs()
        # print(nics)
        # for interface in nics:
        #     print(interface)
        #     psu = psutil.net_if_addrs()[interface]
        #     print(psu)
        #     _logger.info("psu\n%s",
        #                  pprint.pformat(psu))
        # #2
        # ip = get('https://api.ipify.org').content.decode('utf8')
        # print('My public IP address is: {}'.format(ip))
        # _logger.info("My public IP address is: {}\n%s",
        #              pprint.pformat(ip))
        # 3
        # external_ip = urllib.request.urlopen('https://ident.me').read().decode(
        #     'utf8')
        # _logger.info("My external_ip: {}\n%s",
        #              pprint.pformat(external_ip))
        # #4
        # ip_1 = requests.get('https://checkip.amazonaws.com').text.strip()
        # _logger.info("My ip_1: {}\n%s",
        #              pprint.pformat(ip_1))
        # 5
        externalIP = os.popen('curl -s ifconfig.me').readline()
        _logger.info("My external_ip: {}\n%s",
                     pprint.pformat(externalIP))
        url = "https://api.ipify.org?format=json"
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        _logger.info("My external_ip: {}\n%s",
                     pprint.pformat(response.text))
        return request.render("bluemaxpay_account_management.my_merchant_single_sign_on", {
            'pages': request.env['propay.page'].sudo().search([]),
            'bluemaxpay_crumb': 'single_sign_on'
        })

    @route(['/merchant/single_sign_on'], type='http', auth='user', website=True)
    def merchant_single_sign_on(self, **post):
        user = request.env.user
        bluemaxpay_page = request.env['propay.page'].sudo().browse(int(post.get('bluemaxpay'))).bluemaxpay_page
        x509_cert = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.x509_cert') if request.env[
            'ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.x509_cert') else ''
        baseurl = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        class_str = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str') if request.env[
            'ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.class_str') else ''
        device_str = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.device_str') if request.env[
            'ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.device_str') else ''
        cert_str = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str') if request.env[
            'ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.cert_str') else ''
        term_id = request.env['ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id') if request.env[
            'ir.config_parameter'].sudo().get_param(
            'bluemaxpay_account_management.term_id') else ''
        if post.get('bluemaxpay'):
            url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
            payload = "<?xml version='1.0'?>\n" \
                      "<!DOCTYPE Request.dtd>\n" \
                      "<XMLRequest>\n " \
                      "<certStr>{certStr}</certStr>\n " \
                      "<termid>{termid}</termid>\n " \
                      "<class>partner</class>\n " \
                      "<XMLTrans>\n " \
                      "<transType>300</transType>\n " \
                      "<accountNum>{accountNum}</accountNum>\n " \
                      "<ReferrerUrl>{ReferrerUrl}</ReferrerUrl>\n " \
                      "<IpAddress>{IpAddress}</IpAddress>\n " \
                      "<IpSubnetMask>{IpSubnetMask}</IpSubnetMask>\n " \
                      "</XMLTrans>\n" \
                      "</XMLRequest>".format(class_str, device_str, certStr=cert_str, termid=term_id,
                                             accountNum=user.account_number, ReferrerUrl=baseurl,
                                             IpAddress=post.get('ip'), IpSubnetMask=post.get('ip'))
            headers = {
                'X509Certificate': x509_cert,
                'Content-Type': 'application/xml',
            }
            response = requests.request("GET", url, headers=headers, data=payload)
            xml_data = xml.dom.minidom.parseString(response.content)
            xml_string = xml_data.toprettyxml()
            tree = etree.fromstring(xml_string)
            dic = dictlist(tree)
            XMLTrans = dic['XMLResponse'][0]['XMLTrans']
            status = ''
            AuthToken = ''
            for trans in XMLTrans:
                if trans[0] == 'AuthToken':
                    AuthToken = trans[1]
                if trans[0] == 'status':
                    status = trans[1]
            if status == '00':
                url = "https://propay.merchant-portals.com/{Page}?authToken={authToken}&accountnum={accountnum}" \
                    .format(Page=bluemaxpay_page, authToken=AuthToken,
                            accountnum=user.account_number)
                return request.render(
                    "bluemaxpay_account_management.merchant_single_sign_on_redirect", {
                        'url_bluemax': url,
                        'bluemaxpay_crumb': 'single_sign_on'
                    }
                )
