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


class DocumentUplaod(models.TransientModel):
    _name = 'document.upload'
    _rec_name = 'account_number'
    _description = 'document upload'

    account_number = fields.Char('Account Number')
    document_name = fields.Char('Document Name')
    doc_category = fields.Char('Doc Category', default="Underwriting")
    document = fields.Binary('Document', required=True)
    doc_type = fields.Char('Document Type', default='Doc')

    def upload_document_propay(self):
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
                  "</XMLRequest>"\
            .format(class_str, device_str, certStr=cert_str, termid=term_id, accountNum=self.account_number,
                    DocumentName=self.document_name, DocCategory=self.doc_category, DocType=self.doc_type,
                    Document=self.document.decode('ascii'))

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

        if status == '189':
            raise UserError(_("Invalid Account Category"))
        elif status != '00':
            error_id = self.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                             error_id.propay_notes if error_id.propay_notes else '')))
