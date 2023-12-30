from odoo import models, fields, _
import requests

import xml.dom.minidom
from lxml import etree

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


class RenewAccount(models.TransientModel):
    _name = 'renew.account'

    account_number = fields.Char('Account Number')
    tier = fields.Char('Tier')
    cc_num = fields.Char('ccNum')
    exp_date = fields.Char("expDate")
    zip = fields.Integer('Zip')
    cvv2 = fields.Integer('CVV2')

    def renew_account(self):
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
                    "<XMLRequest>\n" \
                    "<certStr>{certStr}</certStr>\n" \
                    "<termid>{termid}</termid>\n" \
                    "<class>partner</class>\n" \
                    "<XMLTrans>\n" \
                        "<transType>39</transType>\n" \
                        "<accountNum>{accountNum}</accountNum>\n" \
                        "<tier>{tier}</tier>\n" \
                        "<ccNum>{ccNum}</ccNum>\n" \
                        "<expDate>{expDate}</expDate>\n" \
                        "<zip>{zip}</zip>\n" \
                        "<CVV2>{CVV2}</CVV2>\n" \
                    "</XMLTrans>\n" \
                    "</XMLRequest>"\
            .format(class_str, device_str, certStr=cert_str, termid=term_id, accountNum=self.account_number,
                    tier=self.tier, ccNum=self.cc_num, expDate=self.exp_date, zip=self.zip, CVV2=self.cvv2)

        headers = {
            'Content-Type': 'application/xml'
        }

        response = requests.request("GET", url, headers=headers, data=payload)

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
        if status != '00':
            error_id = self.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                             error_id.propay_notes if error_id.propay_notes else '')))

