from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ConstructionObject(models.Model):
    # Создаем объект для объектов строительства
    _name = "construction.object"
    _description = "The list of construction objects"
    _order = "name"

    name = fields.Char("Название объекта", required=True)
