from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transport = fields.Many2one('fleet.vehicle', string="Transport")