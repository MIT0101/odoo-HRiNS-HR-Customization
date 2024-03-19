import logging
import base64
import io
import datetime
import pytz
import xlsxwriter
from dateutil import relativedelta

from odoo import models, fields, api, _

from ..utils import datetime_utils as d_utils

_logger = logging.getLogger(__name__)


class HrEmployeeAttendanceLeaveInfoWizard(models.TransientModel):
    _name = 'hr.employee.attendance.leave.info.wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def download_attendance_leave_info_xls(self):
        if self.env.context.get('active_model') == 'hr.employee':
            employees_ids = self.env.context.get('active_ids')

        if not employees_ids:
            return False

        employees = self.env['hr.employee'].browse(employees_ids)

        output_obj, worksheet = self._get_employees_attendance_leave_info(employees, self.start_date, self.end_date)
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
        sheet.write('C1', 'Department')
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
        date_range = d_utils.generate_date_range(start_date, end_date)
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
            ## add attendance info to emp_dict
            for attendance in emp_attendances:
                check_in_date = d_utils.get_date_time_from_user_tz(attendance['check_in'], user_tz).date()
                emp_dict[check_in_date] = {
                    "check_in": d_utils.format_date_time(attendance['check_in'], user_tz),
                    "check_out": d_utils.format_date_time(attendance['check_out'], user_tz),
                    "worked_hours": attendance['worked_hours']
                }

            ## add time off info to emp_dict
            for time_off in emp_time_offs:

                time_off_dict = {
                    "date_from": d_utils.format_date_time(time_off['date_from'], user_tz),
                    "date_to": d_utils.format_date_time(time_off['date_to'], user_tz),
                    "time_off_type": time_off['holiday_status_id'][1],
                    "duration_display": time_off['duration_display']
                }
                date_from_date = d_utils.get_date_time_from_user_tz(time_off['date_from'], user_tz).date()
                # _logger.info(f"emp id {employee.id} date_from_date {date_from_date} time_off_dict {time_off_dict}")
                if emp_dict.get(date_from_date):
                    emp_dict[date_from_date].update(time_off_dict)
                else:
                    emp_dict[date_from_date] = time_off_dict

            for date in date_range:

                # _logger.info(f"emp id {employee.id} date {date} emp_dict {emp_dict}")

                sheet.write(row, col, employee.id)
                sheet.write(row, col + 1, employee.name)
                sheet.write(row, col + 2, employee.department_id.name)
                sheet.write(row, col + 3, d_utils.format_date(date))
                if date in emp_dict:
                    sheet.write(row, col + 4, emp_dict[date].get('check_in'))
                    sheet.write(row, col + 5, emp_dict[date].get('check_out'))
                    sheet.write(row, col + 6, emp_dict[date].get('worked_hours'))
                    sheet.write(row, col + 7, emp_dict[date].get('date_from'))
                    sheet.write(row, col + 8, emp_dict[date].get('date_to'))
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
        attachment_obj = self.env['ir.attachment'].sudo().create(
            {'name': file_name, 'type': 'binary', 'datas': result})
        download_url = '/web/content/' + str(attachment_obj.id) + '?download=true'
        return download_url
