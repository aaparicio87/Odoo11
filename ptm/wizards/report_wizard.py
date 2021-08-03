# -*- encoding: utf-8 -*-
from builtins import len
from datetime import datetime
from dateutil import tz
import calendar
import pytz
import logging
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, pycompat

_logger = logging.getLogger(__name__)

class ReporteMesWizard(models.TransientModel):
    _name = 'reporte.wizard'

    @api.model
    def year_selection(self):
        year = 2020  # replace 2000 with your a start year
        year_list = []
        while year != 2100:  # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    years = fields.Selection(year_selection, string="Year", required=True)
    months = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                               ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
                               ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                              string='Month', required=True, )

    @api.multi
    def get_report_calendar(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'years': self.years,
                'months': self.months,
            },
        }

        return self.env.ref('ptm.modelo3_report').report_action(self, data=data)

class ResumenMesWizard(models.TransientModel):
    _name = 'resumen.wizard'

    @api.model
    def year_selection(self):
        year = 2020  # replace 2000 with your a start year
        year_list = []
        while year != 2100:  # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    years = fields.Selection(year_selection, string="Year", required=True)
    months = fields.Selection([('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
                               ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
                               ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December'), ],
                              string='Month', required=True, )
    aspectos_ptm = fields.Text(_("Positive and negative aspects of PTM"), required=True)

    
    @api.multi
    def get_resumen(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'years': self.years,
                'months': self.months,
                'aspectos_ptm': self.aspectos_ptm,
            },
        }

        return self.env.ref('ptm.resumen_report').report_action(self, data=data)



class ReporteMes(models.AbstractModel):
    _name = 'report.ptm.plan_mensual_view'

    @api.model
    def get_date_day(self, day, month, year):

        date_str = year + '-'+month + '-'+str(day)
        date_utc = datetime.strptime(date_str, '%Y-%m-%d')
        return date_utc

    @api.model
    def get_user_calendar_attendee(self):
        # Dominio-de-Filtro
        domain = [('id','=',self.env.user.id)]
        res_user = self.env['res.users']
        user = res_user.search(domain)

        domain_attendee = [('partner_id','=',user.partner_id.id)]
        calendar_attendee = self.env['calendar.attendee']

        attendees = calendar_attendee.search(domain_attendee)

        return attendees
        
    @api.model
    def get_report_values(self, docids, data=None):
        years = data['form']['years']
        months = data['form']['months']

        from_zone = tz.tzutc()
        mytz = pytz.timezone('America/Havana')

        docs = []
        principal_events = []
        week1 = [{}, {}, {}, {}, {}, {}, {}]
        week2 = [{}, {}, {}, {}, {}, {}, {}]
        week3 = [{}, {}, {}, {}, {}, {}, {}]
        week4 = [{}, {}, {}, {}, {}, {}, {}]
        week5 = [{}, {}, {}, {}, {}, {}, {}]
        week6 = [{}, {}, {}, {}, {}, {}, {}]

        # get the last day of a month's year
        last_day_month = calendar.monthrange(int(years), int(months))[1]

        search_date_str = years+'-'+months+'-01 00:00:00'
        search_date_end_str = years+'-'+months+'-'+str(last_day_month)+' 23:59:59'

        start_date_utc = datetime.strptime(search_date_str, '%Y-%m-%d %H:%M:%S')
        end_date_utc = datetime.strptime(search_date_end_str, '%Y-%m-%d %H:%M:%S')

        start_search_txt = datetime.strftime(start_date_utc, '%d-%m-%Y %H:%M:%S')
        stop_search_txt = datetime.strftime(end_date_utc, '%d-%m-%Y %H:%M:%S')

        start_week_month_search = int(start_date_utc.strftime("%W"))+1
        end_week_month_search = int(end_date_utc.strftime("%W"))+1

        cant_sem = (end_week_month_search - start_week_month_search)+1

        # First Day of the week's month
        first_day_week_month = start_date_utc.strftime("%A")

        calendar_attendee = self.get_user_calendar_attendee()
        
        arr_events_attendees = []

        arr_id_events_attendees = []

        for calendar_attendee_events in calendar_attendee:
            arr_events_attendees.append(calendar_attendee_events.event_id)

        for calendar_id_attendee_events in calendar_attendee:
            arr_id_events_attendees.append(calendar_id_attendee_events.event_id.id)

        # Dominio-de-Filtro
        domain = [('start', '>=', search_date_str), ('stop','<=',search_date_end_str)]
        domain1 = [('start', '>=', search_date_str), ('stop','<=',search_date_end_str),('rrule','!=','')]

        calendar_event = self.env['calendar.event']
        events = calendar_event.search(domain, order="start") 
        events_rr = calendar_event.search(domain1, order="start")

        arr_events_user = []

        for err in events_rr:
            vi = str(err.id)
            i_d = vi.split('-')

            if int(i_d[0]) in arr_id_events_attendees:
                arr_events_user.append(err)
        
        for event in events:
            if event in arr_events_attendees:
                arr_events_user.append(event)


        if arr_events_user:

            for event in arr_events_user:

                """"Convertir fecha string en formato datetime Y-m-d H-M-S"""
                event_start_utc = datetime.strptime(event.start, '%Y-%m-%d %H:%M:%S')
                event_stop_utc = datetime.strptime(event.stop, '%Y-%m-%d %H:%M:%S')

                """"Fecha UTC"""
                event_start_utc = event_start_utc.replace(tzinfo=from_zone)
                event_stop_utc = event_stop_utc.replace(tzinfo=from_zone)

                """"Esatblecer fecha en uso Horario de Cuba"""
                event_start_locale = event_start_utc.astimezone(mytz)
                event_stop_locale = event_stop_utc.astimezone(mytz)

                """"Fecha de Cuba en string"""
                event_start_txt = datetime.strftime(event_start_locale, DEFAULT_SERVER_DATETIME_FORMAT)
                event_stop_txt = datetime.strftime(event_start_locale, DEFAULT_SERVER_DATETIME_FORMAT)

                """" Dia de la semana(Lunes, martes...)"""
                event_day_of_week = event_start_locale.strftime("%A")
                event_number_day_week = event_start_locale.strftime("%w")
                event_week_of_month = int(event_start_locale.strftime("%W"))+1

                if event.principal:
                    frequency = event.rrule_type
                    if frequency == 'daily':
                        frequency = 'Diaria'
                    elif frequency == 'weekly':
                        frequency = 'Semanal el '+ event_day_of_week
                    elif frequency == 'monthly':
                        if event.month_by == 'date':
                            frequency = 'Mensual'
                        else:
                            orden = event.byday
                            if orden == '1':
                                orden = 'Primer'
                            elif orden == '3':
                                orden = 'Tercer'
                            if event.week_list == 'MO':
                                w_list = 'Lunes'
                            elif event.week_list == 'TU':
                                w_list = 'Martes'
                            elif event.week_list == 'WE':
                                w_list = 'Miércoles'    
                            elif event.week_list == 'TH':
                                w_list = 'Jueves'
                            elif event.week_list == 'FR':
                                w_list = 'Viernes'
                            elif event.week_list == 'SA':
                                w_list = 'Sábado'
                            elif event.week_list == 'SU':
                                w_list = 'Domingo'
                            frequency = 'Mensual el '+orden+' '+w_list
                    else:
                        frequency = 'Anualmente'

                    cont = 0
                    if len(principal_events):
                        for principal in principal_events:
                            if principal['name'] == event.name:
                                cont = cont + 1
                        if cont == 0:
                            principal_events.append({
                            'id': event.id,
                            'name': event.name,
                            'frequency': frequency,
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M"),
                            'location': event.location,
                        })
                    else:
                        principal_events.append({
                            'id': event.id,
                            'name': event.name,
                            'frequency': frequency,
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M"),
                            'location': event.location,
                        })

                if event_number_day_week == '1':

                    if event_week_of_month == start_week_month_search:
                        monday = []
                        monday_event = {
                            'id': event.id,
                            'day': event_start_locale.strftime("%d"),
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                            'name': event.name,
                        }
                        if len(week1[0]):
                            if week1[0][0]['day'] == event_start_locale.strftime("%d"):
                                week1[0].append(monday_event)
                        else:
                            monday.append(monday_event)
                            week1[0] = monday
                    elif start_week_month_search < event_week_of_month <= end_week_month_search:
                        no_week = (event_week_of_month - start_week_month_search) + 1
                        if no_week == 2:
                            monday = []
                            monday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week2[0]):
                                if week2[0][0]['day'] == event_start_locale.strftime("%d"):
                                    week2[0].append(monday_event)
                            else:
                                monday.append(monday_event)
                                week2[0] = monday
                        elif no_week == 3:
                            monday = []
                            monday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week3[0]):
                                if week3[0][0]['day'] == event_start_locale.strftime("%d"):
                                    week3[0].append(monday_event)
                            else:
                                monday.append(monday_event)
                                week3[0] = monday
                        elif no_week == 4:
                            monday = []
                            monday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week4[0]):
                                if week4[0][0]['day'] == event_start_locale.strftime("%d"):
                                    week4[0].append(monday_event)
                            else:
                                monday.append(monday_event)
                                week4[0] = monday
                        elif no_week == 5:
                            monday = []
                            monday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week5[0]):
                                if week5[0][0]['day'] == event_start_locale.strftime("%d"):
                                    week5[0].append(monday_event)
                            else:
                                monday.append(monday_event)
                                week5[0] = monday
                        elif no_week == 6:
                            monday = []
                            monday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week6[0]):
                                if week6[0][0]['day'] == event_start_locale.strftime("%d"):
                                    week6[0].append(monday_event)
                            else:
                                monday.append(monday_event)
                                week6[0] = monday

                elif event_number_day_week == '2':
                    if event_week_of_month == start_week_month_search:
                        tuesday = []
                        tuesday_event = {
                            'id': event.id,
                            'day': event_start_locale.strftime("%d"),
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                            'name': event.name,
                        }
                        if len(week1[1]):
                            if week1[1][0]['day'] == event_start_locale.strftime("%d"):
                                week1[1].append(tuesday_event)
                        else:
                            tuesday.append(tuesday_event)
                            week1[1] = tuesday
                    elif start_week_month_search < event_week_of_month <= end_week_month_search:
                        no_week = (event_week_of_month - start_week_month_search) + 1
                        if no_week == 2:
                            tuesday = []
                            tuesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week2[1]):
                                if week2[1][0]['day'] == event_start_locale.strftime("%d"):
                                    week2[1].append(tuesday_event)
                            else:
                                tuesday.append(tuesday_event)
                                week2[1] = tuesday
                        elif no_week == 3:
                            tuesday = []
                            tuesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week3[1]):
                                if week3[1][0]['day'] == event_start_locale.strftime("%d"):
                                    week3[1].append(tuesday_event)
                            else:
                                tuesday.append(tuesday_event)
                                week3[1] = tuesday
                        elif no_week == 4:
                            tuesday = []
                            tuesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }

                            if len(week4[1]):
                                if week4[1][0]['day'] == event_start_locale.strftime("%d"):
                                    week4[1].append(tuesday_event)
                            else:
                                tuesday.append(tuesday_event)
                                week4[1] = tuesday
                        elif no_week == 5:
                            tuesday = []
                            tuesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week5[1]):
                                if week5[1][0]['day'] == event_start_locale.strftime("%d"):
                                    week5[1].append(tuesday_event)
                            else:
                                tuesday.append(tuesday_event)
                                week5[1] = tuesday
                        elif no_week == 6:
                            tuesday = []
                            tuesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week6[1]):
                                if week6[1][0]['day'] == event_start_locale.strftime("%d"):
                                    week6[1].append(tuesday_event)
                            else:
                                tuesday.append(tuesday_event)
                                week6[1] = tuesday

                elif event_number_day_week == '3':
                    if event_week_of_month == start_week_month_search:
                        wednesday = []
                        wednesday_event = {
                            'id': event.id,
                            'day': event_start_locale.strftime("%d"),
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                            'name': event.name,
                        }
                        if len(week1[2]):
                            if week1[2][0]['day'] == event_start_locale.strftime("%d"):
                                week1[2].append(wednesday_event)
                        else:
                            wednesday.append(wednesday_event)
                            week1[2] = wednesday
                    elif start_week_month_search < event_week_of_month <= end_week_month_search:
                        no_week = (event_week_of_month - start_week_month_search) + 1
                        if no_week == 2:
                            wednesday = []
                            wednesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week2[2]):
                                if week2[2][0]['day'] == event_start_locale.strftime("%d"):
                                    week2[2].append(wednesday_event)
                            else:
                                wednesday.append(wednesday_event)
                                week2[2] = wednesday
                        elif no_week == 3:
                            wednesday = []
                            wednesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week3[2]):
                                if week3[2][0]['day'] == event_start_locale.strftime("%d"):
                                    week3[2].append(wednesday_event)
                            else:
                                wednesday.append(wednesday_event)
                                week3[2] = wednesday
                        elif no_week == 4:
                            wednesday = []
                            wednesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week4[2]):
                                if week4[2][0]['day'] == event_start_locale.strftime("%d"):
                                    week4[2].append(wednesday_event)
                            else:
                                wednesday.append(wednesday_event)
                                week4[2] = wednesday
                        elif no_week == 5:
                            wednesday = []
                            wednesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week5[2]):
                                if week5[2][0]['day'] == event_start_locale.strftime("%d"):
                                    week5[2].append(wednesday_event)
                            else:
                                wednesday.append(wednesday_event)
                                week5[2] = wednesday
                        elif no_week == 6:
                            wednesday = []
                            wednesday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week6[2]):
                                if week6[2][0]['day'] == event_start_locale.strftime("%d"):
                                    week6[2].append(wednesday_event)
                            else:
                                wednesday.append(wednesday_event)
                                week6[2] = wednesday

                elif event_number_day_week == '4':
                    if event_week_of_month == start_week_month_search:
                        thursday = []
                        thursday_event = {
                            'id': event.id,
                            'day': event_start_locale.strftime("%d"),
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                            'name': event.name,
                        }
                        if len(week1[3]):
                            if week1[3][0]['day'] == event_start_locale.strftime("%d"):
                                week1[3].append(thursday_event)
                        else:
                            thursday.append(thursday_event)
                            week1[3] = thursday

                    elif start_week_month_search < event_week_of_month <= end_week_month_search:
                        no_week = (event_week_of_month - start_week_month_search) + 1
                        if no_week == 2:
                            thursday = []
                            thursday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week2[3]):
                                if week2[3][0]['day'] == event_start_locale.strftime("%d"):
                                    week2[3].append(thursday_event)
                            else:
                                thursday.append(thursday_event)
                                week2[3] = thursday
                        elif no_week == 3:
                            thursday = []
                            thursday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week3[3]):
                                if week3[3][0]['day'] == event_start_locale.strftime("%d"):
                                    week3[3].append(thursday_event)
                            else:
                                thursday.append(thursday_event)
                                week3[3] = thursday
                        elif no_week == 4:
                            thursday = []
                            thursday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week4[3]):
                                if week4[3][0]['day'] == event_start_locale.strftime("%d"):
                                    week4[3].append(thursday_event)
                            else:
                                thursday.append(thursday_event)
                                week4[3] = thursday
                        elif no_week == 5:
                            thursday = []
                            thursday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week5[3]):
                                if week5[3][0]['day'] == event_start_locale.strftime("%d"):
                                    week5[3].append(thursday_event)
                            else:
                                thursday.append(thursday_event)
                                week5[3] = thursday
                        elif no_week == 6:
                            thursday = []
                            thursday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week6[3]):
                                if week6[3][0]['day'] == event_start_locale.strftime("%d"):
                                    week6[3].append(thursday_event)
                            else:
                                thursday.append(thursday_event)
                                week6[3] = thursday

                elif event_number_day_week == '5':
                    if event_week_of_month == start_week_month_search:
                        friday = []
                        friday_event = {
                            'id': event.id,
                            'day': event_start_locale.strftime("%d"),
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                            'name': event.name,
                        }
                        if len(week1[4]):
                            if week1[4][0]['day'] == event_start_locale.strftime("%d"):
                                week1[4].append(friday_event)
                        else:
                            friday.append(friday_event)
                            week1[4] = friday

                    elif start_week_month_search < event_week_of_month <= end_week_month_search:
                        no_week = (event_week_of_month - start_week_month_search) + 1
                        if no_week == 2:
                            friday = []
                            friday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week2[4]):
                                if week2[4][0]['day'] == event_start_locale.strftime("%d"):
                                    week2[4].append(friday_event)
                            else:
                                friday.append(friday_event)
                                week2[4] = friday
                        elif no_week == 3:
                            friday = []
                            friday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week3[4]):
                                if week3[4][0]['day'] == event_start_locale.strftime("%d"):
                                    week3[4].append(friday_event)
                            else:
                                friday.append(friday_event)
                                week3[4] = friday
                        elif no_week == 4:
                            friday = []
                            friday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week4[4]):
                                if week4[4][0]['day'] == event_start_locale.strftime("%d"):
                                    week4[4].append(friday_event)
                            else:
                                friday.append(friday_event)
                                week4[4] = friday
                        elif no_week == 5:
                            friday = []
                            friday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week5[4]):
                                if week5[4][0]['day'] == event_start_locale.strftime("%d"):
                                    week5[4].append(friday_event)
                            else:
                                friday.append(friday_event)
                                week5[4] = friday
                        elif no_week == 6:
                            friday = []
                            friday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week6[4]):
                                if week6[4][0]['day'] == event_start_locale.strftime("%d"):
                                    week6[4].append(friday_event)
                            else:
                                friday.append(friday_event)
                                week6[4] = friday

                elif event_number_day_week == '6':
                    if event_week_of_month == start_week_month_search:
                        saturday = []
                        saturday_event = {
                            'id': event.id,
                            'day': event_start_locale.strftime("%d"),
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                            'name': event.name,
                        }
                        if len(week1[5]):
                            if week1[5][0]['day'] == event_start_locale.strftime("%d"):
                                week1[5].append(saturday_event)
                        else:
                            saturday.append(saturday_event)
                            week1[5] = saturday

                    elif start_week_month_search < event_week_of_month <= end_week_month_search:
                        no_week = (event_week_of_month - start_week_month_search) + 1
                        if no_week == 2:
                            saturday = []
                            saturday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week2[5]):
                                if week2[5][0]['day'] == event_start_locale.strftime("%d"):
                                    week2[5].append(saturday_event)
                            else:
                                saturday.append(saturday_event)
                                week2[5] = saturday
                        elif no_week == 3:
                            saturday = []
                            saturday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week3[5]):
                                if week3[5][0]['day'] == event_start_locale.strftime("%d"):
                                    week3[5].append(saturday_event)
                            else:
                                saturday.append(saturday_event)
                                week3[5] = saturday
                        elif no_week == 4:
                            saturday = []
                            saturday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week4[5]):
                                if week4[5][0]['day'] == event_start_locale.strftime("%d"):
                                    week4[5].append(saturday_event)
                            else:
                                saturday.append(saturday_event)
                                week4[5] = saturday
                        elif no_week == 5:
                            saturday = []
                            saturday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week5[5]):
                                if week5[5][0]['day'] == event_start_locale.strftime("%d"):
                                    week5[5].append(saturday_event)
                            else:
                                saturday.append(saturday_event)
                                week5[5] = saturday
                        elif no_week == 6:
                            saturday = []
                            saturday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week6[5]):
                                if week6[5][0]['day'] == event_start_locale.strftime("%d"):
                                    week6[5].append(saturday_event)
                            else:
                                saturday.append(saturday_event)
                                week6[5] = saturday

                else:
                    if event_week_of_month == start_week_month_search:
                        sunday = []
                        sunday_event = {
                            'id': event.id,
                            'day': event_start_locale.strftime("%d"),
                            'day_week': event_start_locale.strftime("%A"),
                            'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                            'name': event.name,
                        }
                        if len(week1[6]):
                            if week1[6][0]['day'] == event_start_locale.strftime("%d"):
                                week1[6].append(sunday_event)
                        else:
                            sunday.append(sunday_event)
                            week1[6] = sunday

                    elif start_week_month_search < event_week_of_month <= end_week_month_search:
                        no_week = (event_week_of_month - start_week_month_search) + 1
                        if no_week == 2:
                            sunday = []
                            sunday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week2[6]):
                                if week2[6][0]['day'] == event_start_locale.strftime("%d"):
                                    week2[6].append(saturday_event)
                            else:
                                sunday.append(sunday_event)
                                week2[6] = sunday
                        elif no_week == 3:
                            sunday = []
                            sunday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week3[6]):
                                if week3[6][0]['day'] == event_start_locale.strftime("%d"):
                                    week3[6].append(sunday_event)
                            else:
                                sunday.append(sunday_event)
                                week3[6] = sunday
                        elif no_week == 4:
                            sunday = []
                            sunday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week4[6]):
                                if week4[6][0]['day'] == event_start_locale.strftime("%d"):
                                    week4[6].append(sunday_event)
                            else:
                                sunday.append(sunday_event)
                                week4[6] = sunday
                        elif no_week == 5:
                            sunday = []
                            sunday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week5[6]):
                                if week5[6][0]['day'] == event_start_locale.strftime("%d"):
                                    week5[6].append(sunday_event)
                            else:
                                sunday.append(sunday_event)
                                week5[6] = sunday
                        elif no_week == 6:
                            sunday = []
                            sunday_event = {
                                'id': event.id,
                                'day': event_start_locale.strftime("%d"),
                                'day_week': event_start_locale.strftime("%A"),
                                'hour': event_start_locale.strftime("%H:%M")+'-'+event_stop_locale.strftime("%H:%M"),
                                'name': event.name,
                            }
                            if len(week6[6]):
                                if week6[6][0]['day'] == event_start_locale.strftime("%d"):
                                    week6[6].append(sunday_event)
                            else:
                                sunday.append(sunday_event)
                                week6[6] = sunday

        cant_day = last_day_month
        date_now = self.get_date_day(cant_day, months, years)
        month = date_now.strftime("%B")
        while cant_day != 0:
            date_now = self.get_date_day(cant_day, months, years)
            date_now_week = int(date_now.strftime("%W")) + 1
            week = (date_now_week - start_week_month_search)+1
            day_week = date_now.strftime("%A")
            number_day_week = date_now.strftime("%w")
            week_day = date_now.strftime("%d")

            if week == 6:
                if number_day_week == '1':
                    if not len(week6[0]):
                        week6[0] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '2':
                    if not len(week6[1]):
                        week6[1] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '3':
                    if not len(week6[2]):
                        week6[2] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '4':
                    if not len(week6[3]):
                        week6[3] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '5':
                    if not len(week6[4]):
                        week6[4] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '6':
                    if not len(week6[5]):
                        week6[5] = [{'day': week_day, 'day_week': day_week}]
                else:
                    if not len(week6[6]):
                        week6[6] = [{'day': week_day, 'day_week': day_week}]
                cant_day -= 1

            elif week == 5:
                if number_day_week == '1':
                    if not len(week5[0]):
                        week5[0] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '2':
                    if not len(week5[1]):
                        week5[1] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '3':
                    if not len(week5[2]):
                        week5[2] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '4':
                    if not len(week5[3]):
                        week5[3] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '5':
                    if not len(week5[4]):
                        week5[4] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '6':
                    if not len(week5[5]):
                        week5[5] = [{'day': week_day, 'day_week': day_week}]
                else:
                    if not len(week5[6]):
                        week5[6] = [{'day': week_day, 'day_week': day_week}]
                cant_day -= 1

            elif week == 4:
                if number_day_week == '1':
                    if not len(week4[0]):
                        week4[0] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '2':
                    if not len(week4[1]):
                        week4[1] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '3':
                    if not len(week4[2]):
                        week4[2] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '4':
                    if not len(week4[3]):
                        week4[3] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '5':
                    if not len(week4[4]):
                        week4[4] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '6':
                    if not len(week4[5]):
                        week4[5] = [{'day': week_day, 'day_week': day_week}]
                else:
                    if not len(week4[6]):
                        week4[6] = [{'day': week_day, 'day_week': day_week}]
                cant_day -= 1

            elif week == 3:
                if number_day_week == '1':
                    if not len(week3[0]):
                        week3[0] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '2':
                    if not len(week3[1]):
                        week3[1] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '3':
                    if not len(week3[2]):
                        week3[2] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '4':
                    if not len(week3[3]):
                        week3[3] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '5':
                    if not len(week3[4]):
                        week3[4] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '6':
                    if not len(week3[5]):
                        week3[5] = [{'day': week_day, 'day_week': day_week}]
                else:
                    if not len(week3[6]):
                        week3[6] = [{'day': week_day, 'day_week': day_week}]
                cant_day -= 1

            elif week == 2:
                if number_day_week == '1':
                    if not len(week2[0]):
                        week2[0] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '2':
                    if not len(week2[1]):
                        week2[1] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '3':
                    if not len(week2[2]):
                        week2[2] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '4':
                    if not len(week2[3]):
                        week2[3] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '5':
                    if not len(week2[4]):
                        week2[4] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '6':
                    if not len(week2[5]):
                        week2[5] = [{'day': week_day, 'day_week': day_week}]
                else:
                    if not len(week2[6]):
                        week2[6] = [{'day': week_day, 'day_week': day_week}]
                cant_day -= 1

            else:
                if number_day_week == '1':
                    if not len(week1[0]):
                        week1[0] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '2':
                    if not len(week1[1]):
                        week1[1] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '3':
                    if not len(week1[2]):
                        week1[2] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '4':
                    if not len(week1[3]):
                        week1[3] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '5':
                    if not len(week1[4]):
                        week1[4] = [{'day': week_day, 'day_week': day_week}]
                elif number_day_week == '6':
                    if not len(week1[5]):
                        week1[5] = [{'day': week_day, 'day_week': day_week}]
                else:
                    if not len(week1[6]):
                        week1[6] = [{'day': week_day, 'day_week': day_week}]
                cant_day -= 1

        if cant_sem == 6:
            docs = [week1, week2, week3, week4, week5, week6]
        elif cant_sem == 5:
            docs = [week1, week2, week3, week4, week5]
        else:
            docs = [week1, week2, week3, week4]
        # Gets the manager of the department
        manager_department = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).parent_id.name
        if not manager_department:
            manager_department = ""
            
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'docs': docs,
            'month': month.capitalize(),
            'principal_events': principal_events,
            'manager': manager_department.capitalize(),
        }


class ResumenMes(models.AbstractModel):
    _name = 'report.ptm.resumen_plan_mensual_view'

    @api.model
    def get_user_calendar_attendee(self):
        # Dominio-de-Filtro
        domain = [('id','=',self.env.user.id)]
        res_user = self.env['res.users']
        user = res_user.search(domain)

        domain_attendee = [('partner_id','=',user.partner_id.id)]
        calendar_attendee = self.env['calendar.attendee']

        attendees = calendar_attendee.search(domain_attendee)

        return attendees

    @api.model
    def get_date_day(self, day, month, year):

        date_str = year + '-'+month + '-'+str(day)
        date_utc = datetime.strptime(date_str, '%Y-%m-%d')
        return date_utc

    @api.model
    def get_report_values(self, docids, data=None):

        years = data['form']['years']
        months = data['form']['months']
        aspectos_ptm = data['form']['aspectos_ptm']

        from_zone = tz.tzutc()
        mitz = pytz.timezone('America/Havana')

        docs = []

        # get the last day of a month's year
        last_day_month = calendar.monthrange(int(years), int(months))[1]

        search_date_str = years+'-'+months+'-01 00:00:00'
        search_date_end_str = years+'-'+months+'-'+str(last_day_month)+' 23:59:59'

        start_date_utc = datetime.strptime(search_date_str, '%Y-%m-%d %H:%M:%S')
        end_date_utc = datetime.strptime(search_date_end_str, '%Y-%m-%d %H:%M:%S')

        start_search_txt = datetime.strftime(start_date_utc, '%d-%m-%Y %H:%M:%S')
        stop_search_txt = datetime.strftime(end_date_utc, '%d-%m-%Y %H:%M:%S')

        calendar_attendee = self.get_user_calendar_attendee()
        
        arr_events_attendees = []

        arr_id_events_attendees = []

        for calendar_attendee_events in calendar_attendee:
            arr_events_attendees.append(calendar_attendee_events.event_id)

        for calendar_id_attendee_events in calendar_attendee:
            arr_id_events_attendees.append(calendar_id_attendee_events.event_id.id)

        # Dominio-de-Filtro
        domain = [('start', '>=', search_date_str), ('stop','<=',search_date_end_str)]
        domain1 = [('start', '>=', search_date_str), ('stop','<=',search_date_end_str),('rrule','!=','')]

        calendar_event = self.env['calendar.event']
        events = calendar_event.search(domain, order="start") 
        events_rr = calendar_event.search(domain1, order="start")

        arr_events_user = []

        for err in events_rr:
            vi = str(err.id)
            i_d = vi.split('-')

            if int(i_d[0]) in arr_id_events_attendees:
                arr_events_user.append(err)
        
        for event in events:
            if event in arr_events_attendees:
                arr_events_user.append(event)

        cant_event = len(arr_events_user)
        cant_cumplidos = 0
        cant_incumplidas = 0
        cant_modificadas = 0
        cant_extra_plan =0
        arr_events_suspend = []
        arr_events_modified = []
        arr_events_extra = []

        if len(arr_events_user):
            for event in arr_events_user:
                    if event.suspendida:
                        arr_events_suspend.append({'name': event.name, 'motive': event.motivo_suspendida})
                    if event.extra_plan:
                        cant_extra_plan += 1
                        arr_events_extra.append({'name': event.name, 'motive': event.motivo_extra_plan})
                    if event.modificada:
                        cant_modificadas += 1
                        arr_events_modified.append({'name': event.name, 'motive': event.motivo_modificada})
                    if event.cumplida:
                        cant_cumplidos += 1
                    else:
                        cant_incumplidas += 1

        if len(arr_events_suspend):
            res = []
            for ev in arr_events_suspend:
                if ev not in res:
                    res.append(ev)
            arr_events_suspend = res 
        

        if len(arr_events_extra):
            res = []
            for ev in arr_events_extra:
                if ev not in res:
                    res.append(ev)
            arr_events_extra = res 
            cant_extra_plan = len(res)
        
        if len(arr_events_modified):
            res = []
            for ev in arr_events_modified:
                if ev not in res:
                    res.append(ev)
            arr_events_modified = res 
            cant_modificadas = len(res)         


        # Gets the manager of the department
        manager_department = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)]).parent_id.name
        if not manager_department:
            manager_department = ""
        #Gets the month's name and year
        cant_day = last_day_month
        date_now = self.get_date_day(cant_day, months, years)
        month = date_now.strftime("%B")
        year = date_now.strftime("%Y")

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'cant_planificadas': cant_event,
            'cant_cumplidos': cant_cumplidos,
            'cant_incumplidas': cant_incumplidas,
            'cant_modificadas': cant_modificadas,
            'cant_extra_plan': cant_extra_plan,
            'arr_events_suspend': arr_events_suspend,
            'arr_events_modified': arr_events_modified,
            'arr_events_extra': arr_events_extra,
            'start_search': start_search_txt,
            'stop_search': stop_search_txt,
            'manager': manager_department.capitalize(),
            'month': month.capitalize(),
            'year': year,
            'aspectos_ptm': aspectos_ptm,
            }
