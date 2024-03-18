# -*- coding: utf-8 -*-
{
    'name': "HRiNS HR Customization",

    'summary': """
         Module Contains Hrins HR Customization""",

    'description': """
        Module Contains Hrins HR Customization
        1- Add New action to hr.employee model to open wizard to download employees attendance info as excel file
    """,

    'author': "@HRiNS/M.Al-Mustafa",
    'website': "https://hrins.net/",

    'category': 'HR',
    'version': '0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'hr_attendance', 'hr_holidays'],

    # always loaded
    'data': [
        'security/security.xml',  # security groups
        'wizard/hrins_hr_employee_attendance_info_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'application': False,
}
