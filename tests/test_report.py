from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestReport(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(TestReport, self).setUp(*args, **kwargs)
        # Создаем работника
        self.worker = self.env["res.users"].create(
            {
                "name": "Test User",
                "login": "Test.user@test.odoo.com",
                "email": "Test.user@test.odoo.com",
            }
        )
        # Создаем категорию работ и работу
        self.category = self.env["work.category"].create({"name": "test_category"})
        self.work = self.env["work.dict"].create(
            {"name": "test_work", "category_id": self.category.id}
        )
        # Создаем объект строительства
        self.construction_object = self.env["construction.object"].create(
            {"name": "test_object"}
        )
        # Создаем отчет без работ и перемещений
        self.progress_report = self.env["progress.report"].create(
            {
                "client_name": "test_name",
                "weather": "clear",
                "worker_id": self.worker.id,
                "construction_object": self.construction_object.id,
            }
        )
        # Создаем продукт, который будем перемещать
        self.product = self.env["product.template"].create(
            {
                "name": "test_product",
                "detailed_type": "product",
            }
        )
        # Определяем склад, с которого будут перемещения на склад бригады
        self.stock_location = self.env.ref("stock.stock_location_stock")

        # Создаем склад для бригады, получаем значение локации и устанавливаем его значения в глобальную переменную
        self.crew_location = (
            self.env["stock.warehouse"]
            .create(
                {
                    "name": "test WH",
                    "code": "test",
                }
            )
            .view_location_id
        )
        self.env["ir.config_parameter"].set_param(
            "construction.crew_location", str(self.crew_location.id)
        )

        # Добавляем наличие продукта на первом складе
        self.product_update = self.env["stock.quant"]._update_available_quantity(
            self.product, self.stock_location, 25
        )

        # Создаем перемещение на склад бригады
        self.arrivals = [
            {
                "product_id": self.product.id,
                "amount": 5,
                "location_id": self.stock_location.id,
                "record_id": self.progress_report.id,
            },
            {
                "product_id": self.product.id,
                "amount": 10,
                "location_id": self.stock_location.id,
                "record_id": self.progress_report.id,
            },
        ]
        self.product_arrival_ids = self.env["product.arrival"].create(self.arrivals)

        # Создаем расход продукта и списание со склада бригады
        self.consumptions = [
            {
                "product_id": self.product.id,
                "amount": 5,
                "record_id": self.progress_report.id,
            },
            {
                "product_id": self.product.id,
                "amount": 25,
                "record_id": self.progress_report.id,
            },
        ]
        self.product_consumption_ids = self.env["product.consumption"].create(
            self.consumptions
        )

    def test_progress_report(self):
        # Проверка на пустой список работ в отчете
        with self.assertRaises(ValidationError):
            self.progress_report = self.env["progress.report"].create(
                {
                    "client_name": "test_name_2",
                    "weather": "clear",
                    "worker_id": self.worker.id,
                    "construction_object": self.construction_object.id,
                    "work_list_ids": [],
                }
            )

    # Проверяем, что происходит создание отчета изменение его статуса и перемещение
    def test_picking(self):
        # Вызываем метод для согласования отчета, создания перемещений и удаления дубликатов
        self.progress_report.make_approved()
        # Проверяем, что отчет перешел в статус согласован
        self.assertEqual(
            self.progress_report.state,
            "approved",
            "Book state should be changed to 'approved'",
        )

        # Проверяем, что arrivals и consumption создались и создали в свою очередь перемещения
        self.assertTrue(
            self.progress_report.picking_ids,
            "Pickings should exists'",
        )

        # Проверяем, что статус перемещения 'Done'
        for picking in self.progress_report.picking_ids:
            self.assertEqual(picking.state, "done", "Picking state should be 'Done' ")

        # Проверяем, что происходит объединения одинаковых записей и суммирование их значений в arrivals
        self.assertEqual(
            len(self.progress_report.product_arrival_ids),
            1,
            "The same records should be merged",
        )
        self.arrivals_amount = sum([record.get("amount") for record in self.arrivals])
        self.assertEqual(
            self.progress_report.product_arrival_ids.amount,
            self.arrivals_amount,
            "The values should be summed",
        )

        # Проверяем, что происходит объединения одинаковых записей и суммирование их значений в consumptions
        self.assertEqual(
            len(self.progress_report.product_consumption_ids),
            1,
            "The same records should be merged",
        )
        self.consumptions_amount = sum(
            [record.get("amount") for record in self.consumptions]
        )
        self.assertEqual(
            self.progress_report.product_consumption_ids.amount,
            self.consumptions_amount,
            "The values should be summed",
        )

        # Проверка, что значение "Списано" в Consumption создается
        self.assertEqual(
            self.progress_report.product_consumption_ids.write_off,
            self.consumptions_amount,
            "The value 'Списано' should be calculated",
        )

    # Проверяем ограничения для списка работ
    def test_work_list(self):
        # Заполнены не все временные интервалы
        with self.assertRaises(ValidationError):
            self.work_list_ids = self.env["work.list"].create(
                [
                    {
                        "work_name": self.work.id,
                        "start_time": 0.0,
                        "end_time": 23.00,
                        "record_id": self.progress_report.id,
                    }
                ]
            )

        # Присутствуют пересечения во временных интервалах
        with self.assertRaises(ValidationError):
            self.work_list_ids = self.env["work.list"].create(
                [
                    {
                        "work_name": self.work.id,
                        "start_time": 0.0,
                        "end_time": 23.00,
                        "record_id": self.progress_report.id,
                    },
                    {
                        "work_name": self.work.id,
                        "start_time": 22.0,
                        "end_time": 24.00,
                        "record_id": self.progress_report.id,
                    },
                ]
            )

        # Отрицательное значение временного интервала
        with self.assertRaises(ValidationError):
            self.work_list_ids = self.env["work.list"].create(
                [
                    {
                        "work_name": self.work.id,
                        "start_time": -1.0,
                        "end_time": 24.00,
                        "record_id": self.progress_report.id,
                    }
                ]
            )

        # Временной интервал выходит за рамки 24 часов
        with self.assertRaises(ValidationError):
            self.work_list_ids = self.env["work.list"].create(
                [
                    {
                        "work_name": self.work.id,
                        "start_time": 0.0,
                        "end_time": 25.00,
                        "record_id": self.progress_report.id,
                    }
                ]
            )
        # Время начала работ больше, чем время окончания работ
        with self.assertRaises(ValidationError):
            self.work_list_ids = self.env["work.list"].create(
                [
                    {
                        "work_name": self.work.id,
                        "start_time": 24.0,
                        "end_time": 0.00,
                        "record_id": self.progress_report.id,
                    }
                ]
            )

    # Проверка кнопки "Отправить на  согласование"
    def test_button_on_approval(self):
        self.progress_report.change_state_on_approval()
        self.assertEqual(
            self.progress_report.state,
            "on_approval",
            "Book state should be changed to 'on_approval'",
        )

    # Проверка кнопки "Согласовать"
    def test_button_approved(self):
        self.progress_report.change_state_approved()
        self.assertEqual(
            self.progress_report.state,
            "approved",
            "Book state should be changed to 'approved'",
        )
