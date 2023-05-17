# -*- coding: utf-8 -*-
# from odoo import http


# class ScmCountTag(http.Controller):
#     @http.route('/scm_count_tag/scm_count_tag/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/scm_count_tag/scm_count_tag/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('scm_count_tag.listing', {
#             'root': '/scm_count_tag/scm_count_tag',
#             'objects': http.request.env['scm_count_tag.scm_count_tag'].search([]),
#         })

#     @http.route('/scm_count_tag/scm_count_tag/objects/<model("scm_count_tag.scm_count_tag"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('scm_count_tag.object', {
#             'object': obj
#         })
