# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProgressReport(models.Model):
    _name = "progress.report"
    _inherit = ["mail.thread"]
    _description = "Progress Report"

    date_report = fields.Date(
        "Дата заполнения", required=True, default=fields.Date.today
    )
    weather = fields.Selection(
        [
            ("clear", "ясно"),
            ("cloudy", "пасмурно"),
            ("rainy", "дождь"),
            ("snowy", "снег"),
            ("foggy", "туман"),
        ],
        string="Погодные условия",
        required=True,
    )
    client_name = fields.Char("Заказчик", required=True)
    worker_id = fields.Many2one(
        "res.users", string="Ответственный сотрудник", required=True
    )
    work_list_ids = fields.One2many(
        "work.list", "record_id", string="Список работ", required=True
    )
    state = fields.Selection(
        [
            ("new", "Новый"),
            ("on_approval", "На согласовании"),
            ("approved", "Согласован"),
        ],
        default="new",
        string="Статус отчета",
        tracking=True,
    )

    def name_get(self):
        res = []
        for rec in self:
            res.append(
                (rec.id, f"{rec.client_name} - {rec.date_report.strftime('%d/%m/%Y')}")
            )
        return res

    def change_state_on_approval(self):
        self.state = "on_approval"

    def change_state_approved(self):
        self.state = "approved"

    @api.constrains("work_list_ids")
    def check_work_list(self):
        for record in self:
            if not record.work_list_ids:
                raise ValidationError("Список работ должен быть заполнен!")