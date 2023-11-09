from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    crew_location = fields.Many2one("stock.location",string="Склад бригады", config_parameter='construction.crew_location', groups='construction.group_manager')

    def set_values(self):
        self.env['ir.config_parameter'].set_param('construction.crew_location', str(self.crew_location.id))
        res = super(ResConfigSettings, self).set_values()
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        crew_location_str = ICPSudo.get_param('construction.crew_location')
        if crew_location_str:
            res.update(crew_location = int(crew_location_str))
        return res