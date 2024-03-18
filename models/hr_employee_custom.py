import base64
import io
import datetime
import pytz
import xlsxwriter
from dateutil import relativedelta

from odoo import models, fields, api, _

from ..utils import datetime_utils as d_utils


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ## action to download excel file contains list of info about active employees
    def download_attendance_leave_info_this_month_xls_action(self):
        if self.env.context.get('active_model') == 'hr.employee':
            employees_ids = self.env.context.get('active_ids')

        if not employees_ids:
            return False

        employees = self.env['hr.employee'].browse(employees_ids)
        first_day_of_month = datetime.date.today().replace(day=1)
        # first_day_of_month = datetime.date(2024, 1, 1)
        last_day_of_month = first_day_of_month + relativedelta.relativedelta(months=1, days=-1)
        output_obj, worksheet = self._get_employees_attendance_leave_info(employees, first_day_of_month,
                                                                          last_day_of_month)
        download_url = self._store_file(output_obj)
        return {
            'type': 'ir.actions.act_url',
            'url': download_url,
            'target': 'self',
        }

    def _get_employees_attendance_leave_info(self, employees, start_date, end_date):
        user_tz = pytz.timezone(self.env.user.tz or 'UTC')

        # create a workbook and add a worksheet
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('Employees Info')
        # write headers
        sheet.write('A1', 'Employee ID')
        sheet.write('B1', 'Name')
        sheet.write('C1', 'Job Title')
        sheet.write('D1', 'Date')
        sheet.write('E1', 'Check In')
        sheet.write('F1', 'Check Out')
        sheet.write('G1', 'Worked Hours')
        sheet.write('H1', 'Last Time Off Date From')
        sheet.write('I1', 'Last Time Off Date To')
        sheet.write('J1', 'Last Time Off Type')
        sheet.write('K1', 'Last Time Off Duration')
        row = 1
        col = 0
        for employee in employees:
            # order by check_in
            emp_attendances = self.env['hr.attendance'].search_read([('employee_id', '=', employee.id),
                                                                     ('check_in', '>=', start_date),
                                                                     ('check_in', '<=', end_date)],
                                                                    ['employee_id', 'check_in', 'check_out',
                                                                     'worked_hours'])
            emp_time_offs = self.env['hr.leave'].search_read([('employee_id', '=', employee.id),
                                                              ('date_from', '>=', start_date),
                                                              ('date_to', '<=', end_date),
                                                              ('state', '=', 'validate')],
                                                             ['employee_id', 'date_from', 'date_to',
                                                              'holiday_status_id', 'duration_display'])

            emp_dict = {}
            for attendance in emp_attendances:
                check_in_date = fields.Datetime.from_string(attendance['check_in']).date()
                emp_dict[check_in_date] = {"check_in": attendance['check_in'],
                                           "check_out": attendance['check_out'],
                                           "worked_hours": attendance['worked_hours']}
            for time_off in emp_time_offs:
                date_from = fields.Datetime.from_string(time_off['date_from'])
                date_to = fields.Datetime.from_string(time_off['date_to'])
                emp_dict[date_from.date()] = {"date_from": date_from,
                                              "date_to": date_to,
                                              "time_off_type": time_off['holiday_status_id'][1],
                                              "duration_display": time_off['duration_display']}

            date_range = d_utils.generate_date_range(start_date, end_date)
            for date in date_range:

                sheet.write(row, col, employee.id)
                sheet.write(row, col + 1, employee.name)
                sheet.write(row, col + 2, employee.job_title)
                sheet.write(row, col + 3, d_utils.format_date(date))
                if date in emp_dict:
                    sheet.write(row, col + 4, d_utils.format_date_time(emp_dict[date].get('check_in'), user_tz))
                    sheet.write(row, col + 5, d_utils.format_date_time(emp_dict[date].get('check_out'), user_tz))
                    sheet.write(row, col + 6, emp_dict[date].get('worked_hours'))
                    sheet.write(row, col + 7, d_utils.format_date_time(emp_dict[date].get('date_from'), user_tz))
                    sheet.write(row, col + 8, d_utils.format_date_time(emp_dict[date].get('date_to'), user_tz))
                    sheet.write(row, col + 9, emp_dict[date].get('time_off_type'))
                    sheet.write(row, col + 10, emp_dict[date].get('duration_display'))
                row += 1
            row += 1  # add empty row between employees
        workbook.close()
        output.seek(0)
        return output, workbook

    def _store_file(self, output_obj):
        # encode output in base64
        result = base64.b64encode(output_obj.read())
        current_time_str = d_utils.format_date_time(datetime.datetime.now()).replace(" ", "_").replace(":", "-")
        file_name = f"employees_info_{current_time_str}.xlsx"
        attachment_obj = self.env['ir.attachment'].sudo().create({'name': file_name, 'type': 'binary', 'datas': result})
        download_url = '/web/content/' + str(attachment_obj.id) + '?download=true'
        return download_url
