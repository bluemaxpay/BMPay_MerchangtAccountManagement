import requests
import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import xml.dom.minidom
from lxml import etree
from odoo.http import request

_logger = logging.getLogger(__name__)


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


class SingleSignOn(models.TransientModel):
    _name = 'single.sign.on'

    def _default_user_id(self):
        user_id = self.env['res.users'].browse(self._context.get('active_id'))
        return user_id

    user_id = fields.Many2one('res.users', default='_default_user_id')
    referrer_url = fields.Char('Referrer Url')
    ip_address = fields.Char('Ip Address')
    ip_subnet_mask = fields.Char('Ip Subnet Mask')
    report = fields.Char('Report ID')
    transaction_number = fields.Char('Transaction Number')
    page_id = fields.Many2one('propay.page')
    is_report = fields.Boolean()
    page = fields.Selection([('Account/AddUpdateCheckingAccount', 'Account/AddUpdateCheckingAccount'),
                             ('Account/ConfirmValidationDeposits', 'Account/ConfirmValidationDeposits'),
                             ('Account/SendValidationDeposits', 'Account/SendValidationDeposits'),
                             ('Account/AddUpdateFlashFundAccount', 'Account/AddUpdateFlashFundAccount'),
                             ('ManageFunds/TransferFundsToDebitCard', 'ManageFunds/TransferFundsToDebitCard'),
                             ('ManageFunds/TransferFundsToBankAccount', 'ManageFunds/TransferFundsToBankAccount'),
                             ('ManageFunds/TransferFundsToanotherpropayaccount',
                              'ManageFunds/TransferFundsToanotherpropayaccount'),
                             ('ManageFunds/AddFundsToPropayAccount', 'ManageFunds/AddFundsToPropayAccount'),
                             ('ManageFunds/ScheduledTransfers', 'ManageFunds/ScheduledTransfers'),
                             ('Profile/EditBusinessInfo', 'Profile/EditBusinessInfo'),
                             ('Profile/UpdateAddressAndPhone', 'Profile/UpdateAddressAndPhone'),
                             ('Profile/UpdateEmail', 'Profile/UpdateEmail'),
                             ('Profile/UpdatePin', 'Profile/UpdatePin'),
                             ('PaymentMethod/editpaymentmethod', 'PaymentMethod/editpaymentmethod'),
                             ('Document/UploadDocument', 'Document/UploadDocument'),
                             ('Risk/ListChargeBacks', 'Risk/ListChargeBacks'),
                             ('Report/AdvancedTransactionSearch', 'Report/AdvancedTransactionSearch'),
                             ('Report/ConsolidatedFees', 'Report/ConsolidatedFees'),
                             ('Report/LimitsRatesAndFees', 'Report/LimitsRatesAndFees'),
                             ('Report/TransactionDetails', 'Report/TransactionDetails'),
                             ('Report/TransactionReport', 'Report/TransactionReport'),
                             ('Report/SweepReport', 'Report/SweepReport')
                             ])
    embed_code = fields.Html('Embed Code', readonly=True, compute='_compute_embed_code', sanitize=False)
    url = fields.Char('Url')

    @api.onchange('page_id')
    def _onchange_page_id(self):
        # ipaddress = requests.get('https://api.ipify.org').text
        # _logger.info('My public IP address is: {}'.format(ipaddress))
        x509_cert = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.x509_cert')
        baseurl = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        class_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Class String for ProPay')
        cert_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
        if not cert_str and not term_id and not x509_cert:
            raise UserError('Add authentication credentials for ProPay')
        if self.page_id:
            if self.page_id.bluemaxpay_page == 'Report/TransactionDetails':
                self.is_report = True
            url = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.api_url')
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
                      "</XMLRequest>".format(certStr=cert_str, termid=term_id, accountNum=self.user_id.account_number,
                                             ReferrerUrl=baseurl, IpAddress=self.ip_address,
                                             IpSubnetMask=self.ip_address)
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
                    .format(Page=self.page_id.bluemaxpay_page, authToken=AuthToken,
                            accountnum=self.user_id.account_number)
                self.url = url
        else:
            self.url = ''

    @api.depends('page_id', 'url')
    def _compute_embed_code(self):
        self.embed_code = '<iframe src="%s" class="o_wslides_iframe_viewer" allowFullScreen="true" height="%s" width="%s" frameborder="0"></iframe>' % (
            self.url, 650, 900)
