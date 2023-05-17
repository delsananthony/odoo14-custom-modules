# -*- coding: utf-8 -*-
{
    'name': "scm_count_tag",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Delsan Anthony Soliva",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base', 'scm_abc', 'mail'],
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/count_tag_security.xml',
        'security/scm_count_tag_security.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'wizards/count_tag_wizard.xml',
        'views/stock_count_tag_views.xml',
        'views/res_branch_views.xml',
        'views/menu_views.xml',
        'reports/count_tag_report.xml',
    ],
    # only loaded in demonstration mode
    'installable': True,
    'application': True,
    'auto_install': False,
}
