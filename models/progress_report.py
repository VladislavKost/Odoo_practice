# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProgressReport(models.Model):
    # Класс создает объект для описания отчетов о проделанной работе
    _name = "progress.report"
    _inherit = ["mail.thread"]
    _description = "Progress Report"

    date_report = fields.Date("Дата отчета", required=True, default=fields.Date.today)
    weather = fields.Selection(
        [
            ("clear", "ясно"),
            ("cloudy", "пасмурно"),
            ("foggy", "туман"),
            ("rainy", "дождь"),
            ("snowy", "снег"),
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
    construction_object = fields.Many2one(
        "construction.object", "Объект строительства", required=True
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
    product_arrival_ids = fields.One2many(
        "product.arrival", "record_id", string="Приход продукта"
    )
    product_consumption_ids = fields.One2many(
        "product.consumption", "record_id", string="Расход продукта"
    )

    picking_ids = fields.One2many("stock.picking", "record_id", string="Перемещения")

    def change_state_approved(self):
        # Метод меняет статус отчета на "Согласован"
        self.state = "approved"

    def change_state_on_approval(self):
        # Метод меняет статус отчета на "На согласовании"
        self.state = "on_approval"

    def make_approved(self):
        # Метод создает перемещения между складами, меняет статус отчета на "Согласован"
        # и удаляет дубликаты, объединяя одинаковые записи и суммируя их значения
        self._make_arrival_picking()
        self._make_consumptions_picking()
        self.change_state_approved()
        self.remove_duplicates(self.product_arrival_ids)
        self.remove_duplicates(self.product_consumption_ids, consumption=True)

    def name_get(self):
        # Метод определяет то, как будет отображаться имя отчета
        res = []
        for rec in self:
            res.append(
                (rec.id, f"{rec.client_name} - {rec.date_report.strftime('%d/%m/%Y')}")
            )
        return res

    @api.constrains("work_list_ids")
    def _check_work_list(self):
        # Метод проверяет, заполнены ли работы в форме отчета
        for record in self:
            if not record.work_list_ids:
                raise ValidationError("Список работ должен быть заполнен!")

    def _make_arrival_picking(self):
        # Метод создает словарь с данными о продукте, который приехал на склад бригады,
        # для создания перемещения между складами
        crew_location = self.env["stock.location"].search([("name", "like", "brig")])
        # Заполняем словарь данными о складе и продукте
        data_for_picking = {}
        arrivals = self.product_arrival_ids
        for arrival in arrivals:
            product_id = arrival.product_id
            product_qty = arrival.amount
            location_id = arrival.location_id
            stock_picking_type_id = (
                self.env["stock.picking.type"]
                .search(
                    [
                        ("warehouse_id", "=", location_id.warehouse_id.id),
                        ("sequence_code", "=", "INT"),
                    ]
                )
                .id
            )
            move_data = (
                0,
                0,
                {
                    "name": "constr",
                    "product_id": product_id.id,
                    "product_uom_qty": product_qty,
                    "location_id": location_id.id,
                    "location_dest_id": crew_location.id,
                },
            )
            if not data_for_picking.get(location_id, None):
                data_for_picking.update(
                    {
                        location_id: {
                            "record_id": self.id,
                            "location_id": location_id.id,
                            "location_dest_id": crew_location.id,
                            "picking_type_id": stock_picking_type_id,
                            "move_ids": [move_data],
                        }
                    }
                )
            else:
                data_for_picking.get(location_id).get("move_ids").append(move_data)

        # Создаем перемещение и переводим его в состояние "Выполнено"
        self._make_picking(data_for_picking)

    def _make_consumptions_picking(self):
        # Метод создает словарь с данными о продукте, который был использован бригадой,
        # перемещает продукты в виртуальный склад construction
        crew_location = self.env["stock.location"].search([("name", "like", "brig")])
        location_id = self.env.ref("construction.stock_construction_location")
        stock_picking_type_id = (
            self.env["stock.picking.type"]
            .search(
                [
                    ("warehouse_id", "=", crew_location.warehouse_id.id),
                    ("sequence_code", "=", "INT"),
                ]
            )
            .id
        )
        # Заполняем словарь данными о складе и продукте
        data_for_picking = {}
        consumptions = self.product_consumption_ids
        for consumption in consumptions:
            product_id = consumption.product_id
            product_qty = consumption.amount
            move_data = (
                0,
                0,
                {
                    "name": "constr",
                    "product_id": product_id.id,
                    "product_uom_qty": product_qty,
                    "location_id": crew_location.id,
                    "location_dest_id": location_id.id,
                },
            )
            if not data_for_picking.get(location_id, None):
                data_for_picking.update(
                    {
                        location_id: {
                            "record_id": self.id,
                            "location_id": crew_location.id,
                            "location_dest_id": location_id.id,
                            "picking_type_id": stock_picking_type_id,
                            "move_ids": [move_data],
                        }
                    }
                )
            else:
                data_for_picking.get(location_id).get("move_ids").append(move_data)
        self._make_picking(data_for_picking, consumption=True)

    def _make_picking(self, data_for_picking, consumption=False):
        # Метод создает перемещения для продуктов, указанных в data_for_picking
        data_for_picking = [data for data in data_for_picking.values()]
        new_stock_picking = self.env["stock.picking"].create(data_for_picking)
        for stock_picking in new_stock_picking:
            stock_picking.action_confirm()
            product_qty_move_ids = {
                id.product_id.id: id.product_qty for id in stock_picking.move_ids
            }
            for line in stock_picking.move_line_ids:
                line.qty_done = product_qty_move_ids.get(line.product_id.id, 0)
            stock_picking.button_validate()
            if consumption == True:
                self._update_write_off_field(
                    stock_picking.record_id.product_consumption_ids,
                    product_qty_move_ids,
                )

    def remove_duplicates(self, records, consumption=False):
        # Удаляет дубликаты в БД для данного отчета, суммируя количество для одинаковых записей
        grouped_records = {}
        for record in records:
            if consumption:
                key = (record.record_id.id, record.product_id.id)
            else:
                key = (record.record_id.id, record.product_id.id, record.location_id)
            if key in grouped_records:
                grouped_records[key].amount += record.amount
                record.unlink()
            else:
                grouped_records[key] = record

    def _update_write_off_field(self, product_consumption_ids, product_qty_move_ids):
        # Метод добавляет количество в перемещенных продуктов в поле write_off объекта consumption
        for consumption in product_consumption_ids:
            consumption.write_off = product_qty_move_ids.get(
                consumption.product_id.id, 0
            )
