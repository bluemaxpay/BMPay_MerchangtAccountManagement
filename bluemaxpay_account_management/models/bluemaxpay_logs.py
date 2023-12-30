from odoo import fields, models, api


class BlueMaxPayLogs(models.Model):
    _name = "bluemaxpay.logs"
    _description = "Logs"
    _rec_name = "user_id"
    _order = "id desc"

    request_time = fields.Datetime()
    response_time = fields.Datetime()
    request_body = fields.Text()
    response_body = fields.Text()
    user_id = fields.Many2one('res.users', string="User")
