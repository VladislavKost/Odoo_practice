from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transport = fields.Many2one('fleet.vehicle', string="Transport")
    record_id = fields.Many2one("progress.report", string="Номер отчета")