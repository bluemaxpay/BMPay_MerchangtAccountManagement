import requests
from odoo import fields, models, api, _
from odoo.exceptions import UserError
import xml.dom.minidom
from lxml import etree


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


class ACHTransaction(models.TransientModel):
    _name = 'ach.transaction'
    _description = 'ach transaction'

    user_id = fields.Many2one('res.users')
    amount = fields.Char('Amount')
    routing_number = fields.Char('Routing Number')
    account_type = fields.Char('Account Type')
    standard_entry_class_code = fields.Char('StandardEntryClassCode')
    account_name = fields.Char('Account Name')
    inv_num = fields.Char('Inv Num')

    def ach_transaction(self):
        class_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.class_str')
        if not class_str:
            raise UserError('Add Class String for ProPay')

        device_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.device_str')
        if not device_str:
            raise UserError('Add Device String for ProPay')

        cert_str = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.cert_str')
        term_id = self.env['ir.config_parameter'].sudo().get_param('bluemaxpay_account_management.term_id')
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
                  "</XMLRequest>".format(class_str, device_str, certStr=cert_str, termid=term_id, amount=self.amount,
                                         accountNum=self.user_id.account_number, RoutingNumber=self.routing_number,
                                         AccountNumber=self.user_id.account_number, accountType=self.account_type,
                                         StandardEntryClassCode=self.standard_entry_class_code,
                                         accountName=self.account_name, invNum=self.inv_num)
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

        if status != '00':
            error_id = self.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                             error_id.propay_notes if error_id.propay_notes else '')))
