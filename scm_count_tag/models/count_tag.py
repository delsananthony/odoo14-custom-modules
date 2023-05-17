# -*- utf-8 -*-
import binascii
import tempfile
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.http import request
import odoorpc
import math
from datetime import datetime
import base64

LIMIT = 200


class StockCountTag(models.Model):

    _name = 'stock.count.tag'
    _description = 'Count Tag Header Model'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    location = fields.Selection(
        selection=lambda self: self.get_stock_locations())
    count = fields.Integer(default=0)
    line_ids = fields.One2many(
        comodel_name='stock.count.tag.line', inverse_name='stock_count_tag_id')
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.user.company_id.id, 
                                 string="Company", 
                                 required=True,
                                 readonly=True,)

    """
        1. add `def init` to setup db details
    """

    # def init(self):
    #     config = self.env['ir.config_parameter']
    #     host = config.get_param('r_host')
    #     port = config.get_param('r_port')
    #     dbname = config.get_param('r_dbname')
    #     user = config.get_param('r_user')
    #     passwd = config.get_param('r_passwd')
    #     if not all(host, port, dbname, user, passwd):
    #         raise UserError(
    #             _('Please contact Administrator for remote configuration.'))

    def name_get(self):
        params = []
        for rec in self:
            location_name = rec.with_context(model='stock.count.tag', field='location', value=str(rec.location)).get_location_name()
            datestamp = datetime.now().strftime("%d%m%Y")
            params.append((rec.id, "CT-{}{}".format(location_name, datestamp)))
            pass
        return params

    def connect_remote_psycopg2(self):
        # config = self.env['ir.config_parameter']
        # host = config.get_param('r_host')
        # port = config.get_param('r_port')
        # dbname = config.get_param('r_dbname')
        # user = config.get_param('r_user')
        # passwd = config.get_param('r_passwd')

        # odoo = odoorpc.ODOO(host, port=port)
        # odoo.login(dbname, user, passwd)

        odoo = odoorpc.ODOO('172.104.49.92', port=8079)
        odoo.login('muti_live_copy', 'admin', 'Fy4XoyJMFiqukSzH')

        user = odoo.env.user
        print("ODOO_RPC_USER: ", user)

        return odoo

    def get_stock_locations(self):
        odoo = self.connect_remote_psycopg2()
        company_ids = odoo.env['res.company'].search([('name', '!=', 'EPFC')])
        location_id = self.env.user.branch_id.location_id
        print("xself.company_id:", self.company_id)
        print("xbranch_id:", self.env.user.branch_id.location_id)
        # company_id = self.company_id.id
        company_id = self.env.user.company_id.id
        print("company_name:", self.env.user.company_id.name)
        print("company_id:", self.env.user.company_id.id)
        print("user: ", self.env.user)
        locations = []
        locs = odoo.env['stock.location'].search_read(
            [('usage', '=', 'internal'), ('company_id', '=', company_id), ('active', '=', True)])
        for loc in locs:
            loc_name = f"{loc.get('id')}"
            locations.append((loc_name, loc.get('complete_name')))
        return locations

    def get_location_name(self):

        ctx = self._context

        print('xctx:', ctx)

        # test = dict(self._fields['location'].selection).get(self.location)
        # print("xtest:", test)

        model = ctx.get('model')
        field = ctx.get('field')
        value = ctx.get('value')

        print("xmodel:", model)
        print("xfield:", field)
        print("xvalue:", value)

        return _(dict(self.env[model].fields_get(allfields=[field])[field]['selection'])[value])

    @api.onchange('location')
    def onchange_location(self):
        first_index = 0
        conn = request.env['scm.config'].scm_conn()
        cur = conn.cursor()
        cur.execute("""
        SELECT 
            COUNT(tmpl.id)
        FROM product_template tmpl
        INNER JOIN product_product as prod ON prod.product_tmpl_id = tmpl.id
        INNER JOIN stock_quant as quant ON quant.product_id = prod.id
        INNER JOIN stock_location as loc ON loc.id = quant.location_id
        inner join stock_warehouse sw on sw.lot_stock_id = loc.id
        WHERE tmpl.tracking = 'none' 
        AND tmpl.active = true
        AND quant.location_id = %s
        AND quant.quantity > 0
        AND loc.active = true
        AND loc.usage = 'internal'
        """ % int(self.location))
        products = cur.fetchall()
        print("xxproducts:", products)
        self.update({
            'count': products[first_index][first_index]
        })

    def get_ranges(self):
        ranges = []
        records = self.count
        range_count = math.ceil(records / LIMIT)
        record_count = 0

        for batch in range(0, range_count):
            if batch == 0:
                record_count = batch + LIMIT
                print("rec 1: ", batch, "~", record_count)
                ranges.append((batch, "%s ~ %s" % (batch + 1, record_count)))
            else:
                res = (
                    record_count + LIMIT) > records and records or record_count + LIMIT
                print("rec: ", batch, "~", res)
                ranges.append((record_count, "%s ~ %s" %
                               (record_count + 1, res)))
                record_count = record_count + LIMIT

        return ranges

    @api.onchange('count')
    def create_lines(self):
        index, description = 0, 1
        range_ids = [(5, 0, 0)]
        for rec in self.get_ranges():
            range_ids.append((0, 0, {
                'stock_count_tag_id': self.id,
                'ranges': rec[description],
                'range_value': rec[index],
            }))
        self.line_ids = range_ids


class StockCountTagLine(models.Model):

    _name = 'stock.count.tag.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Count Tag Line Model'
    _rec_name = 'ranges'

    stock_count_tag_id = fields.Many2one(
        comodel_name='stock.count.tag', string='Count Tag')
    ranges = fields.Char(string='Ranges', tracking=True)
    range_value = fields.Integer(default=0)
    state = fields.Selection(selection=[(
        'unused', 'Unused'), ('used', 'Used')], default='unused', string='Status', tracking=True)
    attachment = fields.Binary(string='Count Tag File', tracking=True, attachment=True)
    filename = fields.Char(string="Count Tag Name", size=64, default="Count Tag")


class CountTagTransient(models.TransientModel):

    _name = 'count.tag.transient'

    stock_count_tag_id = fields.Many2one(
        comodel_name='stock.count.tag', string='Count Tag')
    location = fields.Integer(string="Location")
    series = fields.Integer(string="Series")
    ranges = fields.Many2one(
        comodel_name='stock.count.tag.line', string='Ranges')

    def generate_report(self):
        location_id = self.stock_count_tag_id.location
        print("xlocation_id:", type(location_id))
        print("xlocation_id:", location_id)
        offset = self.ranges.range_value
        conn = request.env['scm.config'].scm_conn()
        cur = conn.cursor()
        cur.execute("""
        select 
             prod.barcode, tmpl.brand, tmpl.name, tmpl.part_number, 'PC' as unit, sw.name as branch_name
        FROM product_template tmpl
        INNER JOIN product_product as prod ON prod.product_tmpl_id = tmpl.id
        INNER JOIN stock_quant as quant ON quant.product_id = prod.id
        INNER JOIN stock_location as loc ON loc.id = quant.location_id
        inner join stock_warehouse sw on sw.lot_stock_id = loc.id
        WHERE tmpl.tracking = 'none' 
        AND tmpl.active = true
        AND quant.location_id = %s
        AND quant.quantity > 0
        AND loc.active = true
        AND loc.usage = 'internal'
        ORDER BY prod.barcode ASC LIMIT %s OFFSET %s """ % (location_id, LIMIT, offset))
        stocks = cur.fetchall()

        records = []
        for stock in stocks:
            records.append({
                'barcode': stock[0],
                'brand': stock[1],
                'name': stock[2],
                'part_number': stock[3],
                'unit': stock[4],
                'branch_name': stock[5],
            })

        series = self.series
        location_name = self.stock_count_tag_id.with_context(
            model='stock.count.tag', field='location', value=str(location_id)).get_location_name()
        for rec in records:
            seq_name = "%s-%s" % (location_name.split("/")
                                  [0], str(series).zfill(8))
            rec.update({'tag_no': seq_name})
            series += 1

        data = {
            'records': records
        }
        # pdf = self.env['ir.report'].sudo().get_pdf(records, 'scm_count_tag.report_count_tag')

        # print("x_pdf: ", pdf)

        report_action = self.env.ref(
            'scm_count_tag.report_count_tag').report_action(self, data=data)
        
        data_format = self.env.ref('scm_count_tag.report_count_tag'). \
            sudo()._render_qweb_pdf(data=data)
        
        # print("xdata_format:", data_format)
        print("report_name:", report_action.get('report_name'))
        print("report_file:", report_action.get('report_file'))

        if report_action:
            self.ranges.write({'state': 'used', 'attachment': base64.encodestring(data_format[0])})

        report_action['close_on_report_download'] = True
        return report_action
    

class BarcodeCountTag(models.Model):

    _name = "count.tag.barcode"

    upload_file = fields.Binary("Upload File",  filters='*.txt' ,readonly=True, copy=True,) 
    text_file_name = fields.Char('File Name')
    file_id = fields.Many2one(comodel_name='count.tag.barcode')
    upload_lines = fields.One2many('count.tag.barcode','file_id','Upload Lines',readonly=True,copy=True)
    count_tag_data_ids = fields.One2many(comodel_name='count.tag.data', inverse_name='barcode_count_tag_id')

    @api.onchange('upload_file' )
    def upload_details(self):    

        if self.upload_file:

            if self._origin.id>0 and len(self.upload_lines)>0:
                raise UserError(_('Already %s this excel is loaded, Delete the excel and upload once again')%(self.excel_name)) 
            
            file_path = tempfile.gettempdir()+'/'+ self.text_file_name 
            file_extn=self.text_file_name.split(".")[1][0:3]
            f = open(file_path,'wb')
            f.write(binascii.a2b_base64(self.upload_lines))
            f.close()  
            # if file_extn not in ('TXT','txt'):
            #     raise UserError(_('Selected Wrong File, Kindly Select the Excel File')) 
            
            f = open(file_path,'r')
            data_lines = f.readlines()

            res=[]
            rcount = 0
            ldata=''
            # Strips the newline character
            for li in data_lines:
                if rcount>=0:
                    ldata = li.strip().split(',')
                    
                    gas_id = self.env['ebs.customer.gas.account'].sudo().search([('name','=',ldata[2]),('state','!=', 'cancel')])
                    
                    if len(gas_id) > 1:
                        gas_id=False
                        context = {
                            'barcode_count_tag_id': self.id,
                            'branch': ldata[0],
                            'barcode': ldata[0],
                            'product': ldata[0],
                            'description': ldata[0],
                            'part_number': ldata[0],
                            'unit': ldata[0],
                        }     

                        res.append(context)
                
                rcount += 1
                # print("Line{}: {}".format(rcount, li.strip().split(',')),'000000000000000000000')  

            self.count_tag_data_ids = res

class CountTagData(models.Model):

    _name = 'count.tag.data'

    barcode_count_tag_id = fields.Many2one(comodel_name='count.tag.barcode')
    branch = fields.Char(string='Branch')
    barcode = fields.Char(string='Barcode')
    product = fields.Char(string='Product')
    description = fields.Char(string='Description')
    part_number = fields.Char(string='Part Number')
    unit = fields.Char(string='Unit')



