from odoo import api, fields, models


class VirtualConstructionLocation(models.Model):
    _inherit = "res.company"

    def _create_construction_location(self):
        # Создаем объект для создания виртуальной локации construction, в которую будут перемещаться списанные продукты
        parent_location = self.env.ref(
            "stock.stock_location_locations_virtual", raise_if_not_found=False
        )
        for company in self:
            construction_location = self.env["stock.location"].create(
                {
                    "name": "Construction",
                    "usage": "construction",
                    "location_id": parent_location.id,
                    "company_id": company.id,
                }
            )
            self.env["ir.property"]._set_default(
                "property_stock_construction",
                "product.template",
                construction_location,
                company.id,
            )

    @api.model
    def create_missing_construction_location(self):
        # Добавляет локацию при установке модуля для уже существующих компаний
        company_ids = self.env["res.company"].search([])
        construction_product_template_field = self.env["ir.model.fields"]._get(
            "product.template", "property_stock_construction"
        )
        companies_having_property = (
            self.env["ir.property"]
            .sudo()
            .search(
                [
                    ("fields_id", "=", construction_product_template_field.id),
                    ("res_id", "=", False),
                ]
            )
            .mapped("company_id")
        )
        company_without_property = company_ids - companies_having_property
        company_without_property._create_construction_location()

    def _create_per_company_locations(self):
        super(VirtualConstructionLocation, self)._create_per_company_locations()
        self._create_construction_location()


class Location(models.Model):
    # Добавляем виртуальную локацию в поле usage модели stock.location
    _inherit = "stock.location"

    usage = fields.Selection(
        selection_add=[("construction", "Construction")],
        ondelete={"construction": "cascade"},
    )
