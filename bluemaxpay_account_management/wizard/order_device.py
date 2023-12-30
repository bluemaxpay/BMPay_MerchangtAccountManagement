import requests

from odoo import fields, models, api, _
from odoo.exceptions import UserError
import xml.dom.minidom
from lxml import etree
import requests


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


class OrderDevice(models.TransientModel):
    _name = "order.device"

    user_id = fields.Many2one('res.users')
    ship_to = fields.Char('Ship To', related="user_id.partner_id.name", store=True, readonly=False)
    ship_to_contact = fields.Char('ship To Contact', related="user_id.partner_id.name", store=True, readonly=False)
    ship_to_address = fields.Char('ship To Address', related="user_id.partner_id.propay_apartment_number", store=True, readonly=False)
    ship_to_address2 = fields.Char('ship To Address2', related="user_id.partner_id.propay_address", store=True, readonly=False)
    ship_to_city = fields.Char('ship To City', related="user_id.partner_id.propay_city", store=True, readonly=False)
    ship_to_state = fields.Char('ship To State', related="user_id.partner_id.propay_state", store=True, readonly=False)
    ship_to_zip = fields.Char('ship To Zip', related="user_id.partner_id.propay_zip", store=True, readonly=False)
    ship_to_phone = fields.Char('ship To Phone', related="user_id.partner_id.day_phone", store=True, readonly=False)
    # cardholder_name = fields.Char('cardholder name')
    # cc_num = fields.Char('Cc Num')
    # exp_date = fields.Char('Exp Date')
    # CVV2 = fields.Char('CVV2')
    # billing_zip = fields.Char('Billing Zip')
    # device_name = fields.Char('Name')
    propay_device_id = fields.Many2one('propay.device', string="Device")
    device_nickname = fields.Char("Nickname")
    qty = fields.Integer('Quantity')

    def order_device(self):
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
                  "<certStr>{certStr}</certStr>\n" \
                  "<termid>{termid}</termid>\n" \
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
                  "<Devices>\n " \
                  "<Device>\n" \
                  "<Name>{DeviceName}</Name>\n " \
                  "<Quantity>{Quantity}</Quantity>\n " \
                  "</Device>\n " \
                  "</Devices>\n" \
                  "</XMLTrans>\n" \
                  "</XMLRequest>".format(certStr=cert_str, termid=term_id, accntNum=self.user_id.account_number,
                                         shipTo=self.ship_to, shipToContact=self.ship_to_contact,
                                         shipToAddress=self.ship_to_address, shipToAddress2=self.ship_to_address2,
                                         shipToCity=self.ship_to_city, shipToState=self.ship_to_state,
                                         shipToZip=self.ship_to_zip, shipToPhone=self.ship_to_phone,
                                         DeviceName=self.propay_device_id.name, Quantity=self.qty)

        # payload = "<?xml version='1.0'?>\n" \
        #           "<!DOCTYPE Request.dtd>\n" \
        #           "<XMLRequest>\n " \
        #           "<certStr>%s</certStr>\n " \
        #           "<termid>%s</termid>\n " \
        #           "<class>partner</class>\n " \
        #           "<XMLTrans>\n " \
        #           "<transType>430</transType>\n " \
        #           "<accntNum>%s</accntNum>\n " \
        #           "<shipTo>%s</shipTo>\n " \
        #           "<shipToContact>%s</shipToContact>\n " \
        #           "<shipToAddress>%s</shipToAddress>\n " \
        #           "<shipToAddress2>%s</shipToAddress2>\n " \
        #           "<shipToCity>%s</shipToCity>\n " \
        #           "<shipToState>%s</shipToState>\n " \
        #           "<shipToZip>%s</shipToZip>\n " \
        #           "<shipToPhone>%s</shipToPhone>\n " \
        #           "<cardholderName>%s</cardholderName>\n " \
        #           "<CcNum>%s</CcNum>\n " \
        #           "<ExpDate>%s</ExpDate>\n " \
        #           "<CVV2>%s</CVV2>\n " \
        #           "<billingZip>%s</billingZip>\n " \
        #           "<PostbackUrl>https://apis-sit.globalpay.com/ucp/postback/merchants\n /platform/eyJtY3NfcmF3X2RhdGEiOnsibW1hX2lkIjoiTU1BXzBm\n M TA0ZjYxMTk4ODQ5MDE4ZjI1NWYzNjRlN2M0ZDllIiwicHJvZHVjdC\n I6W10sIm1jc19tZXJjaGFudF9pZCI6Ik1FUl9kODdkOGE1NmI4YzQ0\n ZjVkYWY1YzEw NzExZDkw YzA0M iJ9LCJYLUdQLVZlcnNpb24iOiIyMDIxLTAzLTIyIiwibV9hcHBfaWQiOiJqd0VrTUo4bUNYRVVQNkVXdjUw\n OFc2WU1qNXpQSlNOVyIsInhfZ2xvYmFsX3RyYW5zYWN0aW9uX2lkIj\n oicnJ0LWY5ZGI5OTk3LWI2ZTgtNDUzZS1iNWEyLTlhNmJiNTMxNGJj\n M mY4bDh1In0=</PostbackUrl>\n " \
        #           "<PostbackUrl2>https://apis-sit.globalpay.com/ucp/postback/merchants/platform/\n eyJtY3NfcmF3X2RhdGEiOnsibW1hX2lkIjoiTU1BXzBmMTA0ZjYxMTk4ODQ5MDE\n 4ZjI1NWYzNjRlN2M 0ZDllIiwicHJvZHVjdCI6W10sIm1jc19tZXJjaGFudF9pZC\n I6Ik1FUl9kODdkOGE1NmI4YzQ0ZjVkYWY1YzEw NzExZDkwYzA0MiJ9LCJYLUdQL\n VZlcnNpb24iOiIyMDIxLTAzLTIyIiwibV9hcHBfaWQiOiJqd0VrTUo4bUNYRVVQ\n NkVXdjUw OFc2WU1qNXpQSlNOVyIsInhfZ2xvYmFsX3RyYW5zYWN0aW9uX2lkIjo\n icnJ0LWY5ZGI5OTk3LWI2ZTgtNDUzZS1iNWEyLTlhNmJiNTMxNGJjMmY4b\n Dh1In0=</PostbackUrl2>\n " \
        #           "<Devices>\n " \
        #           "<Device>\n" \
        #           "<Name>%s</Name>\n " \
        #           "<Quantity>%s</Quantity>\n " \
        #           "<Attributes>\n " \
        #           "<Item Name=\"Heartland.AMD.OfficeKey\" Value=\"45\"/>\n " \
        #           "</Attributes>\n " \
        #           "</Device>\n " \
        #           "</Devices>\n" \
        #           "</XMLTrans>\n" \
        #           "</XMLRequest>" % (class_str, device_str, cert_str, term_id, self.user_id.account_number, self.ship_to, self.ship_to_contact,
        #                              self.ship_to_address, self.ship_to_address2, self.ship_to_city, self.ship_to_state,
        #                              self.ship_to_zip, self.ship_to_phone, self.cardholder_name, self.cc_num,
        #                              self.exp_date,
        #                              self.CVV2, self.billing_zip, self.device_name, self.qty)
        headers = {
            'Content-Type': 'application/xml',
        }
        response = requests.request("GET", url, headers=headers, data=payload)

        xml_data = xml.dom.minidom.parseString(response.content)  # Prepare xml DOM Structure
        xml_string = xml_data.toprettyxml()  # it is used to print the xml in standard format
        tree = etree.fromstring(xml_string)  # Tree to string
        dic = dictlist(tree)  # Dictionary List
        XMLTrans = dic['XMLResponse'][0]['XMLTrans']
        status = ''
        for trans in XMLTrans:
            if trans[0] == 'status':
                status = trans[1]
                for qty in range(1, self.qty + 1):
                    self.user_id.partner_id.write({
                        'partner_device_ids': [(0, 0, {
                            'name': self.propay_device_id.id,
                            'nickname': self.device_nickname,
                        })]
                    })
                break
        if status != '00':
            error_id = self.env['propay.error.codes'].sudo().search(
                [('propay_status_code', '=', int(status))], limit=1)
            raise UserError(_("{}:{}".format(error_id.propay_value if error_id.propay_value else '',
                                             error_id.propay_notes if error_id.propay_notes else '')))
