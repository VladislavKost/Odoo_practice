# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProgressReport(models.Model):
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
        self.state = "approved"

    def change_state_on_approval(self):
        self.state = "on_approval"

    def make_approved(self):
        self.change_state_approved()
        self._make_arrival_picking()
        self._make_consumptions_picking()
        self.remove_duplicates("product.arrival")
        self.remove_duplicates("product.consumption")

    def name_get(self):
        res = []
        for rec in self:
            res.append(
                (rec.id, f"{rec.client_name} - {rec.date_report.strftime('%d/%m/%Y')}")
            )
        return res

    @api.constrains("work_list_ids")
    def _check_work_list(self):
        for record in self:
            if not record.work_list_ids:
                raise ValidationError("Список работ должен быть заполнен!")

    def _make_arrival_picking(self):
        # Получаем id склада бригады
        brigada_location = self.env["stock.location"].search([("name", "like", "brig")])
        stock_picking_type_id = 5

        for record in self:
            # Заполняем словарь данными о складе и продукте
            data_for_picking = {}
            arrivals = self.env["product.arrival"].search(
                [("record_id", "=", record.id)]
            )
            for arrival in arrivals:
                product_id = arrival.product_id
                product_qty = arrival.amount
                location_id = arrival.location_id

                if not data_for_picking.get(location_id, None):
                    data_for_picking.update(
                        {
                            location_id: {
                                "record_id": record.id,
                                "location_id": location_id.id,
                                "location_dest_id": brigada_location.id,
                                "picking_type_id": stock_picking_type_id,
                                "move_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "name": "constr",
                                            "product_id": product_id.id,
                                            "product_uom_qty": product_qty,
                                            "location_id": location_id.id,
                                            "location_dest_id": brigada_location.id,
                                        },
                                    )
                                ],
                            }
                        }
                    )
                else:
                    data_for_picking.get(location_id).get("move_ids").append(
                        (
                            0,
                            0,
                            {
                                "name": "constr",
                                "product_id": product_id.id,
                                "product_uom_qty": product_qty,
                                "location_id": location_id.id,
                                "location_dest_id": brigada_location.id,
                            },
                        )
                    )

        # Создаем перемещение и переводим его в состояние "Выполнено"
        self._make_picking(data_for_picking)

    def _make_consumptions_picking(self):
        brigada_location = self.env["stock.location"].search([("name", "like", "brig")])
        location_id = self.env.ref("construction.stock_construction_location")
        stock_picking_type_id = 5

        for record in self:
            # Заполняем словарь данными о складе и продукте
            data_for_picking = {}
            consumptions = self.env["product.consumption"].search(
                [("record_id", "=", record.id)]
            )
            for consumption in consumptions:
                product_id = consumption.product_id
                product_qty = consumption.amount

                if not data_for_picking.get(location_id, None):
                    data_for_picking.update(
                        {
                            location_id: {
                                "record_id": record.id,
                                "location_id": brigada_location.id,
                                "location_dest_id": location_id.id,
                                "picking_type_id": stock_picking_type_id,
                                "move_ids": [
                                    (
                                        0,
                                        0,
                                        {
                                            "name": "constr",
                                            "product_id": product_id.id,
                                            "product_uom_qty": product_qty,
                                            "location_id": brigada_location.id,
                                            "location_dest_id": location_id.id,
                                        },
                                    )
                                ],
                            }
                        }
                    )
                else:
                    data_for_picking.get(location_id).get("move_ids").append(
                        (
                            0,
                            0,
                            {
                                "name": "constr",
                                "product_id": product_id.id,
                                "product_uom_qty": product_qty,
                                "location_id": brigada_location.id,
                                "location_dest_id": location_id.id,
                            },
                        )
                    )
        self._make_picking(data_for_picking, consumption=True)

    def _make_picking(self, data_for_picking, consumption=False):
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

    def remove_duplicates(self, transfer):
        grouped_records = {}
        records = self.env[transfer].search([])
        for record in records:
            if transfer == "product.arrival":
                key = (record.record_id.id, record.product_id.id, record.location_id)
            else:
                key = (record.record_id.id, record.product_id.id)
            if key in grouped_records:
                grouped_records[key].amount += record.amount
                record.unlink()
            else:
                grouped_records[key] = record

    def _update_write_off_field(self, product_consumption_ids, product_qty_move_ids):
        for consumption in product_consumption_ids:
            consumption.write_off = product_qty_move_ids.get(
                consumption.product_id.id, 0
            )
