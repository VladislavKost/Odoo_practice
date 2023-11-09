from odoo.tests.common import TransactionCase, tagged


@tagged("-at_install", "post_install")
class TestLocation(TransactionCase):
    def test_construction_location_creation(self):
        self.construction_location = self.env["stock.location"].search(
            [("name", "=", "Construction")]
        )

        self.assertTrue(
            self.construction_location.id, "Construction location should exist"
        )
