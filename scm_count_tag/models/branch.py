from odoo import _, api, models, fields
import odoorpc

class ResPartner(models.Model):

    _inherit = 'res.partner'

    is_branch = fields.Boolean(string='Branch', default=False)

class ResBranch(models.Model):

    _inherit = 'res.branch'
    _rec_name = 'location_name'

    location_id = fields.Integer(string='Location Id')
    location_name = fields.Char(string='Location Name')

    # def init(self):

    #     odoo = odoorpc.ODOO('172.104.49.92', port=8079)
    #     odoo.login('muti_live_copy', 'admin', 'Fy4XoyJMFiqukSzH')
    #     filter = [('usage', '=', 'internal'), ('company_id', '!=', 3), ('active', '=', True)]
    #     location_ids = odoo.env['stock.location'].search(filter)
    #     locations = odoo.env['stock.location'].browse(location_ids)

    #     print("xlocation_ids:", location_ids)
    #     print("xlocations:", locations)

    #     for loc in locations:
    #         print(loc.id)
    #         print(loc.complete_name)
    #         print(loc.company_id)
    #         self.create({
    #             'location_id': loc.id,
    #             'location_name': loc.complete_name,
    #             'branch_code': loc.id,
    #             'parent_id': loc.company_id.id
    #         })


    