from odoo import models, fields, api


class ProductArrival(models.Model):
    _name = "product.arrival"
    _description = "The arrival of products"

    product_id = fields.Many2one("product.template", string="Название продукта")
    amount = fields.Float("Приход", required=True)
    location_id = fields.Many2one("stock.location", string="Склад отправитель")
    record_id = fields.Many2one(
        "progress.report", string="Номер отчета", ondelete="cascade"
    )
    record_state = fields.Selection(string="Статус отчета", related="record_id.state")


class ProductConsumption(models.Model):
    _name = "product.consumption"
    _description = "The consumption of products"

    product_id = fields.Many2one(
        "product.template", string="Название продукта", required=True
    )
    amount = fields.Float("Расход", required=True)
    record_id = fields.Many2one(
        "progress.report", string="Номер отчета", ondelete="cascade"
    )
    write_off = fields.Float("Списано продукта", default=0.0, readonly=True)
    record_state = fields.Selection(string="Статус отчета", related="record_id.state")
