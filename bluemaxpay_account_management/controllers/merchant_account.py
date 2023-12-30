
import base64
import logging
import requests
import xml.dom.minidom
from lxml import etree
from datetime import datetime

from odoo import http, fields, _
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome

_logger = logging.getLogger(__name__)

SIGN_UP_MERCHANT_REQUEST_PARAMS = {'error', 'user_id'}


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
        value = node.text
        res.append({node.tag: value})
    return


class PropayAccount(http.Controller):

    @http.route('/get/blumaxpay/country_code', auth='public', type='json', website=True)
    def get_bluemaxpay_country_code(self, **kw):
        country_states = [dict(id=x.id, name=x.name, code=x.code) for x in
                          [rec for rec in
                           request.env['country.code.propay'].sudo().search(
                               [('propay_code', '=',
                                 kw.get('CountryCode'))]).name.state_ids]]
        return country_states

    @http.route('/propay/account/', auth='public', website=True, csrf=False)
    def propay_account(self, **kw):
        """ Propay Account Page """
        user = request.env['res.users'].sudo().search([('login', '=', kw.get('login'))])
        data = [user.name, kw.get('login'), kw.get('account_number'), user.merchant_password]
        if kw.get('activate') == '00':
            return http.request.render('bluemaxpay_account_management.propay_account', {'data': data})
        elif kw.get('activate') == '66':
            return http.request.render('bluemaxpay_account_management.propay_account_inactive', {'data': data})

    """
    @http.route('/propay/device/', auth='public', type='json', website=True,
                csrf=False)
    def propay_device(self, **kw):
        device = request.env['propay.device'].sudo().search(
            [('id', '=', kw.get('id'))])
        return device.name
    """

    #
    # class PropayPasswordReset(http.Controller):

    @http.route('/propay/merchant/creation/', auth='public', type='http', website=True)
    def propay_merchat_create(self, **kw):
        """ Merchant Account Creation """
        user = request.env['res.users'].sudo().search([('id', '=', kw.get('user_id'))])
        if user.is_merchant:
            return request.render("bluemaxpay_account_management.propay_account_created")
        else:
            return request.render("bluemaxpay_account_management.merchant_account_creation", {'id': kw.get('id')})

    def create_merchant_account(self, kw):
        """ Create Merchant Account """
        class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')

        if not class_str:
            class_str = ''

        # device_str = request.env['ir.config_parameter'].sudo(). \
        #     get_param('bluemaxpay_account_management.device_str')
        device_str = request.env.company.propay_device_id.name
        if not device_str:
            device_str = ''

        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        notification_email = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.notification_email')
        if not cert_str and not term_id:
            cert_str = ''
            term_id = ''
        date_of_birth = ''
        if kw.get('date_of_birth'):
            date = datetime.strptime(str(kw.get('date_of_birth')), '%Y-%M-%d')
            date_of_birth = date.strftime('%M-%d-%Y')
        if kw.get('monthly_bank_card_volume') and kw.get('average_ticket') and kw.get('highest_ticket'):
            monthly_bank_card_volume = kw.get('monthly_bank_card_volume')
            average_ticket = kw.get('average_ticket')
            highest_ticket = kw.get('highest_ticket')
        else:
            monthly_bank_card_volume = 1000
            average_ticket = 100
            highest_ticket = 250
        """
        if kw.get('device'):
            device = request.env['propay.device'].sudo().search(
                [('id', '=', kw.get('device'))])
        """
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')

        certStr = cert_str + ':' + term_id

        certStr_bytes = certStr.encode('ascii')
        certStr_base64_bytes = base64.b64encode(certStr_bytes)
        base64_certStr = certStr_base64_bytes.decode('ascii')
        login = kw.get('login')
        key = kw.keys()
        payload = "a"
        if len(key) != 0:
            payload = "<XMLRequest>\n" \

            if cert_str:
                payload += "<certStr>" + cert_str + "</certStr>\n" \

            if term_id:
                payload += "<termid>" + term_id + "</termid>\n" \

            if class_str:
                payload += "<class>" + class_str + "</class>\n" \

            payload += "<XMLTrans>\n" \
            "<transType>01</transType>\n" \

            if kw.get('login'):
                payload += "<sourceEmail>" + kw.get('login') + "</sourceEmail>\n" \

            if kw.get('first_name'):
                payload += "<firstName>" + kw.get('first_name') + "</firstName>\n" \

            if kw.get('initial'):
                payload += "<mInitial>" + kw.get('initial') + "</mInitial>\n" \

            if kw.get('last_name'):
                payload += "<lastName>" + kw.get('last_name') + "</lastName>\n" \

            if date_of_birth:
                payload += "<dob>" + date_of_birth + "</dob>\n" \

            if kw.get('SocialSecurityNumber'):
                payload += "<ssn>" + kw.get('SocialSecurityNumber') + "</ssn>\n" \

            if kw.get('day_phone'):
                payload += "<dayPhone>" + kw.get('day_phone') + "</dayPhone>\n" \

            if kw.get('phone'):
                payload += "<evenPhone>" + kw.get('phone') + "</evenPhone>\n" \

            if notification_email:
                payload += "<NotificationEmail>" + notification_email + "</NotificationEmail>\n" \

            if kw.get('currency_code'):
                payload += "<currencyCode>" + kw.get('currency_code') + "</currencyCode>\n" \

            if kw.get('tier'):
                payload += "<tier>" + kw.get('tier') + "</tier>\n" \

            if kw.get('address1'):
                payload += "<addr>" + kw.get('address1') + "</addr>\n" \

            if kw.get('apartment_number'):
                payload += "<aptNum>" + kw.get('apartment_number') + "</aptNum>\n" \

            if kw.get('city'):
                payload += "<city>" + kw.get('city') + "</city>\n" \

            if kw.get('state'):
                payload += "<state>" + kw.get('state') + "</state>\n" \

            if kw.get('zip'):
                payload += "<zip>" + kw.get('zip') + "</zip>\n" \

            if kw.get('country'):
                payload += "<country>" + kw.get('country') + "</country>\n" \

            if kw.get('business_legal_name'):
                payload += "<BusinessLegalName>" + kw.get('business_legal_name') + "</BusinessLegalName>\n" \

            if kw.get('doing_business_as'):
                payload += "<DoingBusinessAs>" + kw.get('doing_business_as') + "</DoingBusinessAs>\n" \

            if kw.get('ein'):
                payload += "<EIN>" + kw.get('ein') + "</EIN>\n" \

            if kw.get('MCCCode'):
                payload += "<MCCCode>" + kw.get('MCCCode') + "</MCCCode>\n" \

            if kw.get('WebsiteURL'):
                payload += "<WebsiteURL>" + str(kw.get('WebsiteURL')) + "</WebsiteURL>\n" \

            if kw.get('business_description'):
                payload += "<BusinessDesc>" + kw.get('business_description') + "</BusinessDesc>\n" \

            if kw.get('monthly_bank_card_volume'):
                payload += "<MonthlyBankCardVolume>" + kw.get('monthly_bank_card_volume') + "</MonthlyBankCardVolume>\n" \

            if kw.get('average_ticket'):
                payload += "<AverageTicket>" + kw.get('average_ticket') + "</AverageTicket>\n" \

            if kw.get('highest_ticket'):
                payload += "<HighestTicket>" + kw.get('highest_ticket') + "</HighestTicket>\n" \

            if kw.get('address1'):
                payload += "<BusinessAddress>" + kw.get('address1') + "</BusinessAddress>\n" \

            if kw.get('address2'):
                payload += "<BusinessAddress2>" + kw.get('address2') + "</BusinessAddress2>\n" \

            if kw.get('city'):
                payload += "<BusinessCity>" + kw.get('city') + "</BusinessCity>\n" \

            if kw.get('state'):
                payload += "<BusinessState>" + kw.get('state') + "</BusinessState>\n" \

            if kw.get('country'):
                payload += "<BusinessCountry>" + kw.get('country') + "</BusinessCountry>\n" \

            if kw.get('zip'):
                payload += "<BusinessZip>" + kw.get('zip') + "</BusinessZip>\n" \

            if kw.get('account_country_code'):
                payload += "<AccountCountryCode>" + kw.get('account_country_code') + "</AccountCountryCode>\n" \

            if kw.get('routing_number'):
                payload += "<RoutingNumber>" + kw.get('routing_number') + "</RoutingNumber>\n" \

            if kw.get('bank_account_number'):
                payload += "<AccountNumber>" + kw.get('bank_account_number') + "</AccountNumber>\n" \

            if kw.get('account_ownership_type'):
                payload += "<AccountOwnershipType>" + str(kw.get('account_ownership_type')) + "</AccountOwnershipType>\n" \

            if kw.get('account_type'):
                payload += "<accountType>" + str(kw.get('account_type')) + "</accountType>\n" \

            if kw.get('bank_name'):
                payload += "<BankName>" + kw.get('bank_name') + "</BankName>\n" \

            if kw.get('time_zone'):
                payload += "<TimeZone>" + kw.get('time_zone') + "</TimeZone>\n" \

            payload += "<Devices>\n" \
            "<Device>\n" \

            if device_str:
                payload += "<Name>" + device_str + "</Name>\n" \

            payload += "<Quantity>1</Quantity>\n" \
            "</Device>\n" \
            "</Devices>\n" \
            "<BeneficialOwnerData>\n" \

            if kw.get('OwnerCount'):
                payload += "<OwnerCount>" + kw.get('OwnerCount') + "</OwnerCount>\n" \

            payload += "<Owners>\n" \
            "<Owner>\n" \

            if kw.get('first_name'):
                payload += "<FirstName>" + kw.get('first_name') + "</FirstName>\n" \

            if kw.get('last_name'):
                payload += "<LastName>" + kw.get('last_name') + "</LastName>\n" \

            if kw.get('Title'):
                payload += "<Title>" + str(kw.get('Title')) + "</Title>\n" \

            if kw.get('address1'):
                payload += "<Address>" + kw.get('address1') + "</Address>\n" \

            if kw.get('Percentage'):
                payload += "<Percentage>" + kw.get('Percentage') + "</Percentage>\n" \

            if kw.get('SocialSecurityNumber'):
                payload += "<SSN>" + kw.get('SocialSecurityNumber') + "</SSN>\n" \

            if kw.get('country'):
                payload += "<Country>" + kw.get('country') + "</Country>\n" \

            if kw.get('state'):
                payload += "<State>" + kw.get('state') + "</State>\n" \

            if kw.get('city'):
                payload += "<City>" + kw.get('city') + "</City>\n" \

            if kw.get('zip'):
                payload += "<Zip>" + kw.get('zip') + "</Zip>\n" \

            if kw.get('login'):
                payload += "<Email>" + kw.get('login') + "</Email>\n" \

            if date_of_birth:
                payload += "<DateOfBirth>" + date_of_birth + "</DateOfBirth>\n" \

            payload += "</Owner>\n" \
            "</Owners>\n" \
            "</BeneficialOwnerData>\n" \
            "</XMLTrans>\n" \
            "</XMLRequest>" % ()
            headers = {
                'Authorization': 'Basic ' + base64_certStr,
                'Content-Type': 'application/json'
            }
        result = ''
        if kw.get('checkbox'):

            response = requests.request("GET", url, headers=headers,
                                        data=payload)
            # Convert xml to dict
            xml_data = xml.dom.minidom.parseString(response.content)
            xml_string = xml_data.toprettyxml()
            tree = etree.fromstring(xml_string)
            dic = dictlist(tree)
            status = ''
            sourceEmail = ''
            accntNum = ''
            password = ''
            activate = ''
            XMLTrans = dic['XMLResponse'][0]['XMLTrans']

            status = XMLTrans[1]['status']
            # if status == '65':
            #     status = '00'
            # sourceEmail = XMLTrans[2]['sourceEmail']
            if status == '00':
                sourceEmail = XMLTrans[2]['sourceEmail']
                accntNum = XMLTrans[3]['accntNum']
                password = XMLTrans[5]['password']
                activate = '00'
            if status == '66':
                sourceEmail = XMLTrans[2]['sourceEmail']
                accntNum = XMLTrans[3]['accntNum']
                password = XMLTrans[5]['password']
                activate = '66'
                status = '00'
            result = {
                'Status': status,
                'activate': activate,
                'sourceEmail': sourceEmail,
                'accntNum': accntNum,
                'password': password
            }
        return result

    @http.route('/bluemaxpay/account/create', auth='public', type='http', website=True)
    def bluemax_account_create(self, **kw):
        qcontext = {k: v for (k, v) in request.params.items() if k in SIGN_UP_MERCHANT_REQUEST_PARAMS}
        user = request.env['res.users'].sudo().search([('id', '=', kw.get('user_id'))])
        qcontext_key = kw.keys()
        for rec in qcontext_key:
            qcontext[rec] = kw.get(rec)
        response = self.create_merchant_account(kw)
        if response:
            if response.get('Status') != '00':
                error_id = request.env['propay.error.codes'].sudo().search(
                    [('propay_status_code', '=', int(response.get('Status')))],
                    limit=1)
                # qcontext['error'] = _("Can't Create a Merchant Account.status code is %s" % response.get('Status'))
                qcontext['error'] = _("{}:{}".format(
                    error_id.propay_value if error_id.propay_value else '',
                    error_id.propay_notes if error_id.propay_notes else ''))
                return request.render(
                    "bluemaxpay_account_management.merchant_account_creation",
                    qcontext)
            elif response.get('Status') == '00':
                user.is_merchant = True
                user.partner_id.is_merchant = True
                account_number = str(response.get('accntNum'))
                user.account_number = account_number
                merchant_password = response.get('password')

                user.merchant_password = merchant_password

                # saving bank account details
                user.partner_id.account_country_code = user.encrypt_data(kw.get('account_country_code'))
                user.partner_id.bank_account_number = user.encrypt_data(kw.get('bank_account_number'))
                user.partner_id.routing_number = user.encrypt_data(kw.get('routing_number'))
                user.partner_id.account_ownership_type = user.encrypt_data(str(kw.get('account_ownership_type')))
                user.partner_id.bank_name = user.encrypt_data(kw.get('bank_name'))
                user.partner_id.account_type = user.encrypt_data(str(kw.get('account_type')))

                # saving account details
                user.partner_id.propay_apartment_number = str(kw.get('apartment_number'))
                user.partner_id.propay_address = str(kw.get('address1'))
                user.partner_id.propay_city = kw.get('city')
                user.partner_id.propay_state = kw.get('state')
                user.partner_id.propay_country = kw.get('country')
                user.partner_id.propay_zip = kw.get('zip')
                user.partner_id.first_name = kw.get('first_name')
                user.partner_id.last_name = kw.get('last_name')
                user.partner_id.initial = kw.get('initial')
                user.partner_id.even_phone = kw.get('phone')
                user.partner_id.day_phone = kw.get('day_phone')

                # device = request.env[
                #     'propay.device'].sudo().search(
                #     [('id', '=', kw.get('device'))])
                # device_order = request.env['propay.order.device'].sudo().create(
                #     {
                #         'name': user.name,
                #         'device_id': device.id,
                #         'user_id': user.id
                #     })
                if response.get('activate') == '00':
                    user.merchant_active = 'active'
                    return request.redirect(
                        f"/propay/account/?login={kw.get('login')}&account_number={response.get('accntNum')}&password={response.get('password')}&activate={response.get('activate')}")
                if response.get('activate') == '66':
                    user.merchant_active = 'inactive'
                    return request.redirect(
                        f"/propay/account/?login={kw.get('login')}&account_number={response.get('accntNum')}&password={response.get('password')}&activate={response.get('activate')}")
        else:
            return request.render("bluemaxpay_account_management.merchant_account_creation", qcontext)

    @http.route('/get/bluemax/agreement', auth='public', type='json', website=True)
    def get_bluemaxpay_agreement(self, **kw):
        agreements = request.env['bluemaxpay.agreement'].sudo().search([])
        return len(agreements)

    @http.route('/bluemaxpay/agreement/download/<id>', auth='public', type='http', website=True)
    def bluemaxpay_agreement_download(self, id=None, **kw):
        pdf, _ = request.env['ir.actions.report']._render_qweb_pdf('bluemaxpay_account_management.report_action_agreement_bluemaxpay', int(id))
        pdf_http_headers = [('Content-Type', 'application/pdf'),
                            ('Content-Length', len(pdf)),
                            ('Content-Disposition',
                             'attachment; filename="BlueMaxPay Agreement.pdf"')]
        return request.make_response(pdf, headers=pdf_http_headers)


class ProPaySignUp(AuthSignupHome):

    def update_qcontext(self, kw, qcontext):
        qcontext_key = kw.keys()
        for rec in qcontext_key:
            qcontext[rec] = kw.get(rec)

    def create_merchant_account(self, kw):
        """ Create Merchant Account """
        class_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')

        if not class_str:
            class_str = ''

        # device_str = request.env['ir.config_parameter'].sudo(). \
        #     get_param('bluemaxpay_account_management.device_str')
        device_str = request.env.company.propay_device_id.name
        if not device_str:
            device_str = ''

        tier = request.env.company.propay_tier_id.name
        if not tier:
            tier = ''

        cert_str = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        notification_email = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.notification_email')
        if not cert_str and not term_id and not notification_email:
            cert_str = ''
            term_id = ''
            notification_email = ''
        date_of_birth = ''
        if kw.get('date_of_birth'):
            date = datetime.strptime(str(kw.get('date_of_birth')), '%Y-%M-%d')
            date_of_birth = date.strftime('%M-%d-%Y')
        if kw.get('monthly_bank_card_volume') and kw.get('average_ticket') and kw.get('highest_ticket'):
            monthly_bank_card_volume = kw.get('monthly_bank_card_volume')
            average_ticket = kw.get('average_ticket')
            highest_ticket = kw.get('highest_ticket')
        else:
            monthly_bank_card_volume = 1000
            average_ticket = 100
            highest_ticket = 250
        """
        if kw.get('device'):
            device = request.env['propay.device'].sudo().search(
                [('id', '=', kw.get('device'))])
        """
        url = request.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
        certStr = cert_str + ':' + term_id
        certStr_bytes = certStr.encode('ascii')
        certStr_base64_bytes = base64.b64encode(certStr_bytes)
        base64_certStr = certStr_base64_bytes.decode('ascii')
        login = kw.get('login')
        key = kw.keys()
        if len(key) != 0:
            payload = "<XMLRequest>\n" \

            if cert_str:
                payload += "<certStr>" + cert_str + "</certStr>\n" \

            if term_id:
                payload += "<termid>" + term_id + "</termid>\n" \

            if class_str:
                payload += "<class>" + class_str + "</class>\n" \

            payload += "<XMLTrans>\n" \
            "<transType>01</transType>\n" \

            if kw.get('login'):
                payload += "<sourceEmail>" + kw.get('login') + "</sourceEmail>\n" \

            if kw.get('first_name'):
                payload += "<firstName>" + kw.get('first_name') + "</firstName>\n" \

            if kw.get('initial'):
                payload += "<mInitial>" + kw.get('initial') + "</mInitial>\n" \

            if kw.get('last_name'):
                payload += "<lastName>" + kw.get('last_name') + "</lastName>\n" \

            if date_of_birth:
                payload += "<dob>" + date_of_birth + "</dob>\n" \

            if kw.get('SocialSecurityNumber'):
                payload += "<ssn>" + kw.get('SocialSecurityNumber') + "</ssn>\n" \

            if kw.get('day_phone'):
                payload += "<dayPhone>" + kw.get('day_phone') + "</dayPhone>\n" \

            if kw.get('phone'):
                payload += "<evenPhone>" + kw.get('phone') + "</evenPhone>\n" \

            if notification_email:
                payload += "<NotificationEmail>" + notification_email + "</NotificationEmail>\n" \

            if kw.get('currency_code'):
                payload += "<currencyCode>" + kw.get('currency_code') + "</currencyCode>\n" \

            payload += "<tier>" + tier + "</tier>\n" \

            if kw.get('address1'):
                payload += "<addr>" + kw.get('address1') + "</addr>\n" \

            if kw.get('apartment_number'):
                payload += "<aptNum>" + kw.get('apartment_number') + "</aptNum>\n" \

            if kw.get('city'):
                payload += "<city>" + kw.get('city') + "</city>\n" \

            if kw.get('state'):
                payload += "<state>" + kw.get('state') + "</state>\n" \

            if kw.get('zip'):
                payload += "<zip>" + kw.get('zip') + "</zip>\n" \

            if kw.get('country'):
                payload += "<country>" + kw.get('country') + "</country>\n" \

            if kw.get('business_legal_name'):
                payload += "<BusinessLegalName>" + kw.get('business_legal_name') + "</BusinessLegalName>\n" \

            if kw.get('doing_business_as'):
                payload += "<DoingBusinessAs>" + kw.get('doing_business_as') + "</DoingBusinessAs>\n" \

            if kw.get('ein'):
                ein = ''.join(e for e in kw.get('ein') if e.isalnum())
                payload += "<EIN>" + ein + "</EIN>\n" \

            if kw.get('MCCCode'):
                payload += "<MCCCode>" + kw.get('MCCCode') + "</MCCCode>\n" \

            if kw.get('WebsiteURL'):
                payload += "<WebsiteURL>" + str(kw.get('WebsiteURL')) + "</WebsiteURL>\n" \

            if kw.get('business_description'):
                payload += "<BusinessDesc>" + kw.get('business_description') + "</BusinessDesc>\n" \

            if kw.get('monthly_bank_card_volume'):
                payload += "<MonthlyBankCardVolume>" + kw.get('monthly_bank_card_volume') + "</MonthlyBankCardVolume>\n" \

            if kw.get('average_ticket'):
                payload += "<AverageTicket>" + kw.get('average_ticket') + "</AverageTicket>\n" \

            if kw.get('highest_ticket'):
                payload += "<HighestTicket>" + kw.get('highest_ticket') + "</HighestTicket>\n" \

            if kw.get('address1'):
                payload += "<BusinessAddress>" + kw.get('address1') + "</BusinessAddress>\n" \

            if kw.get('address2'):
                payload += "<BusinessAddress2>" + kw.get('address2') + "</BusinessAddress2>\n" \

            if kw.get('city'):
                payload += "<BusinessCity>" + kw.get('city') + "</BusinessCity>\n" \

            if kw.get('state'):
                payload += "<BusinessState>" + kw.get('state') + "</BusinessState>\n" \

            if kw.get('country'):
                payload += "<BusinessCountry>" + kw.get('country') + "</BusinessCountry>\n" \

            if kw.get('zip'):
                payload += "<BusinessZip>" + kw.get('zip') + "</BusinessZip>\n" \

            if kw.get('account_country_code'):
                payload += "<AccountCountryCode>" + kw.get('account_country_code') + "</AccountCountryCode>\n" \

            if kw.get('routing_number'):
                payload += "<RoutingNumber>" + kw.get('routing_number') + "</RoutingNumber>\n" \

            if kw.get('bank_account_number'):
                payload += "<AccountNumber>" + kw.get('bank_account_number') + "</AccountNumber>\n" \

            if kw.get('account_ownership_type'):
                payload += "<AccountOwnershipType>" + str(kw.get('account_ownership_type')) + "</AccountOwnershipType>\n" \

            if kw.get('account_type'):
                payload += "<accountType>" + str(kw.get('account_type')) + "</accountType>\n" \

            if kw.get('bank_name'):
                payload += "<BankName>" + kw.get('bank_name') + "</BankName>\n" \

            if kw.get('time_zone'):
                payload += "<TimeZone>" + kw.get('time_zone') + "</TimeZone>\n" \

            payload += "<Devices>\n" \
            "<Device>\n" \

            if device_str:
                payload += "<Name>"+ device_str +"</Name>\n" \

            payload += "<Quantity>1</Quantity>\n" \
            "</Device>\n" \
            "</Devices>\n" \
            "<BeneficialOwnerData>\n" \

            if kw.get('OwnerCount'):
                payload += "<OwnerCount>" + kw.get('OwnerCount') + "</OwnerCount>\n" \

            payload += "<Owners>\n" \
            "<Owner>\n" \

            if kw.get('first_name'):
                payload += "<FirstName>" + kw.get('first_name') + "</FirstName>\n" \

            if kw.get('last_name'):
                payload += "<LastName>" + kw.get('last_name') + "</LastName>\n" \

            if kw.get('Title'):
                payload += "<Title>" + str(kw.get('Title')) + "</Title>\n" \

            if kw.get('address1'):
                payload += "<Address>" + kw.get('address1') + "</Address>\n" \

            if kw.get('Percentage'):
                payload += "<Percentage>" + kw.get('Percentage') + "</Percentage>\n" \

            if kw.get('SocialSecurityNumber'):
                payload += "<SSN>" + kw.get('SocialSecurityNumber') + "</SSN>\n" \

            if kw.get('country'):
                payload += "<Country>" + kw.get('country') + "</Country>\n" \

            if kw.get('state'):
                payload += "<State>" + kw.get('state') + "</State>\n" \

            if kw.get('city'):
                payload += "<City>" + kw.get('city') + "</City>\n" \

            if kw.get('zip'):
                payload += "<Zip>" + kw.get('zip') + "</Zip>\n" \

            if kw.get('login'):
                payload += "<Email>" + kw.get('login') + "</Email>\n" \

            if date_of_birth:
                payload += "<DateOfBirth>" + date_of_birth + "</DateOfBirth>\n" \

            payload += "</Owner>\n" \
            "</Owners>\n" \
            "</BeneficialOwnerData>\n" \
            "</XMLTrans>\n" \
            "</XMLRequest>" % ()
            headers = {
                'Authorization': 'Basic ' + base64_certStr,
                'Content-Type': 'application/json'
            }
            result = ''
            if kw.get('checkbox'):
                log_data = {
                    'request_time': fields.Datetime.now(),
                    'user_id': request.env.user.id,
                    'request_body': payload,
                }
                response = requests.request("GET", url, headers=headers, data=payload)
                # Convert xml to dict
                xml_data = xml.dom.minidom.parseString(response.content)
                xml_string = xml_data.toprettyxml()
                log_data.update({
                    'response_time': fields.Datetime.now(),
                    'response_body': xml_string,
                })
                tree = etree.fromstring(xml_string)
                dic = dictlist(tree)
                status = ''
                sourceEmail = ''
                accntNum = ''
                password = ''
                activate = ''
                XMLTrans = dic['XMLResponse'][0]['XMLTrans']
                status = XMLTrans[1]['status']
                # if status == '65':
                #     status = '00'
                # sourceEmail = XMLTrans[2]['sourceEmail']
                if status == '00':
                    sourceEmail = XMLTrans[2]['sourceEmail']
                    accntNum = XMLTrans[3]['accntNum']
                    password = XMLTrans[5]['password']
                    activate = '00'
                if status == '66':
                    sourceEmail = XMLTrans[2]['sourceEmail']
                    accntNum = XMLTrans[3]['accntNum']
                    password = XMLTrans[5]['password']
                    activate = '66'
                    status = '00'
                result = {
                    'Status': status,
                    'activate': activate,
                    'sourceEmail': sourceEmail,
                    'accntNum': accntNum,
                    'password': password,
                    'log_data': log_data,
                }
            return result

    @http.route(['/my/merchant/account/signup'], type='http', auth='user', website=True, sitemap=False)
    def merchant_signup(self, **kwargs):
        qcontext = {}
        if kwargs:
            result = self.create_merchant_account(kwargs)
            if result and result.get('Status') == '00' or not result and not kwargs.get('checkbox'):
                user = request.env.user
                user.is_merchant = True
                user.partner_id.is_merchant = True
                account_number = str(result.get('accntNum'))
                user.account_number = account_number
                merchant_password = result.get('password')
                user.merchant_password = merchant_password

                # saving bank account details
                user.partner_id.account_country_code = user.encrypt_data(kwargs.get('account_country_code'))
                user.partner_id.bank_account_number = user.encrypt_data(kwargs.get('bank_account_number'))
                user.partner_id.routing_number = user.encrypt_data(kwargs.get('routing_number'))
                user.partner_id.account_ownership_type = user.encrypt_data(str(kwargs.get('account_ownership_type')))
                user.partner_id.bank_name = user.encrypt_data(kwargs.get('bank_name'))
                user.partner_id.account_type = user.encrypt_data(str(kwargs.get('account_type')))

                # saving account details
                user.partner_id.propay_apartment_number = str(kwargs.get('apartment_number'))
                user.partner_id.propay_address = str(kwargs.get('address1'))
                user.partner_id.propay_city = kwargs.get('city')
                user.partner_id.propay_state = kwargs.get('state')
                user.partner_id.propay_country = kwargs.get('country')
                user.partner_id.propay_zip = kwargs.get('zip')
                user.partner_id.first_name = kwargs.get('first_name')
                user.partner_id.last_name = kwargs.get('last_name')
                user.partner_id.initial = kwargs.get('initial')
                user.partner_id.even_phone = kwargs.get('phone')
                user.partner_id.day_phone = kwargs.get('day_phone')

                if result.get('activate') == '00':
                    user.merchant_active = 'active'
                    return request.redirect(
                        f"/propay/account/?login={kwargs.get('login')}&account_number={result.get('accntNum')}&password={result.get('password')}&activate={result.get('activate')}")
                if result.get('activate') == '66':
                    user.merchant_active = 'inactive'
                    return request.redirect(
                        f"/propay/account/?login={kwargs.get('login')}&account_number={result.get('accntNum')}&password={result.get('password')}&activate={result.get('activate')}")
            elif result and result.get('Status') != '00':
                request.env['bluemaxpay.logs'].sudo().create(result.get('log_data'))
                self.update_qcontext(kwargs, qcontext)
                error_id = request.env['propay.error.codes'].sudo().search([('propay_status_code', '=', int(result.get('Status')))], limit=1)
                qcontext['error'] = _(
                    "{}:{}".format(
                        error_id.propay_value if error_id.propay_value else '',
                        error_id.propay_notes if error_id.propay_notes else ''))
        if not qcontext:
            qcontext.update({
                'login': request.env.user.partner_id.email
            })
        return request.render('bluemaxpay_account_management.merchant_signup', qcontext)
