from odoo import models, fields, api
from odoo.exceptions import ValidationError


class WorksList(models.Model):
    _name = "work.list"
    _description = "Work List for report"

    category_name = fields.Char("Категория работ", compute="_get_work_category", store=True)
    work_name = fields.Many2one(
        "work.dict", string="Наименование работы", required=True
    )
    start_time = fields.Float("Время начала", required=True)
    end_time = fields.Float("Время окончания", required=True)
    total = fields.Float("Общее время работ", compute="_compute_total")
    record_id = fields.Many2one(
        "progress.report", string="Номер отчета", ondelete="cascade"
    )


    @api.depends("start_time", "end_time")
    def _compute_total(self):
        for record in self:
            if record.end_time > record.start_time:
                record.total = record.end_time - record.start_time
            else:
                record.total = 0

    @api.depends("work_name")
    def _get_work_category(self):
        for record in self:
            record.category_name = record.work_name.category_id.name


    @api.constrains("start_time", "end_time")
    def _check_intervals(self):
        domain = [("record_id", "=", self.record_id.id)]
        work_list = self.search(domain, order="start_time")
        times_list = [(work.start_time, work.end_time) for work in work_list]
        start = 0.0
        if times_list[0][0] != 0:
            raise ValidationError("Работы должны начинаться с 00:00")
        for time in times_list:
            if time[0] == start:
                if time[0] < time[1]:
                    start = time[1]
                else:
                    raise ValidationError(
                        "Время начала работ должно быть меньше времени окончания работ"
                    )
            elif time[0] < 0 or time[0] > 24:
                raise ValidationError("Временной интервал может быть от 0 до 24 часов")
            elif time[0] < start:
                if time[0] > time[1]:
                    raise ValidationError(
                        "Время начала работ должно быть меньше времени окончания работ"
                    )
                else:
                    raise ValidationError(f"Временные интервалы работ пересекаются.")
            else:
                raise ValidationError("Необходимо заполнить все временные интервалы")
        if start != 24:
            if start < 24:
                raise ValidationError("Необходимо заполнить все временные интервалы")
            else:
                raise ValidationError("Временной интервал может быть от 0 до 24 часов")


class WorkCategory(models.Model):
    _name = "work.category"
    _description = "The list of work categories"

    name = fields.Char("Название категории", required=True)
    work_dict_ids = fields.One2many(
        "work.dict", "category_id", string="Наименование работ", required=True
    )
    works_count = fields.Integer("Количество работ в категории", compute="_count_works")
    

    def get_works(self):
        return {
            "name": ("Работы категории"),
            "view_mode": "tree,form",
            "res_model": "work.dict",
            "type": "ir.actions.act_window",
            "domain": [("category_id", "=", self.id)],}

    @api.depends("work_dict_ids")
    def _count_works(self):
        for record in self:
            record.works_count = self.env["work.dict"].search_count(
                [("category_id", "=", self.id)]
            )




class WorkDict(models.Model):
    _name = "work.dict"
    _description = "The list of possible works"

    name = fields.Char("Наименование работы", required=True)
    category_id = fields.Many2one(
        "work.category", string="Название категории", ondelete="cascade", required=True
    )
