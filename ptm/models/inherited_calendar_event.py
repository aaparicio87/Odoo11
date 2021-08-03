# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class Insidencia(models.Model):
    _inherit = 'calendar.event'

    cumplida = fields.Boolean(_('Task Accomplished'))
    principal = fields.Boolean(_('Principal Task'))
    suspendida = fields.Boolean(_('Suspended Task'))
    motivo_suspendida = fields.Text(_('Who originated them (Causes)?'))
    extra_plan = fields.Boolean(_('Extra Plan Task'))
    motivo_extra_plan = fields.Text(_('Who originated them (Causes)?'))
    modificada = fields.Boolean(_('Modified Task'))
    motivo_modificada = fields.Text(_('Who originated them (Causes)?'))

    creada = fields.Boolean(_('Task Created'))
    ocd = fields.Many2one('calendar.ocd', string='OCD')
    cocd = fields.Boolean(compute='_compute_ocd', string='OCD_Compute', default=False, store=True)

    
    @api.depends('ocd')
    def _compute_ocd(self):

        for event in self:
            if event.ocd:
                event.cocd = True
       
    
class OCD(models.Model):
    
    _name = 'calendar.ocd'
    _description = 'Create an OCD'


    principal = fields.Boolean(_('Principal Task'))
    name = fields.Char(_('Name'), required=True)
    acronym = fields.Char(_('Acronym'), required=True)
    job_ids = fields.Many2many('hr.job', string=_('Members'), required=True)
    start_datetime = fields.Datetime(_('Start DateTime'), required=True)
    stop_datetime = fields.Datetime(_('End Datetime'), required=True)
    location = fields.Char(_('Location'))
    ocd_flag = fields.Integer('Create ocd in event')

    # RECURRENCE FIELD
    rrule = fields.Char('Recurrent Rule', compute='_compute_rrule', inverse='_inverse_rrule', store=True)
    rrule_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)')
    ], string='Recurrence', help="Let the event automatically repeat at that interval")
    recurrency = fields.Boolean('Recurrent', help="Recurrent Meeting")
    recurrent_id = fields.Integer('Recurrent ID')
    recurrent_id_date = fields.Datetime('Recurrent ID date')
    end_type = fields.Selection([
        ('count', 'Number of repetitions'),
        ('end_date', 'End date')
    ], string='Recurrence Termination', default='count')
    interval = fields.Integer(string='Repeat Every', default=1, help="Repeat every (Days/Week/Month/Year)")
    count = fields.Integer(string='Repeat', help="Repeat x times", default=1)
    mo = fields.Boolean('Mon')
    tu = fields.Boolean('Tue')
    we = fields.Boolean('Wed')
    th = fields.Boolean('Thu')
    fr = fields.Boolean('Fri')
    sa = fields.Boolean('Sat')
    su = fields.Boolean('Sun')
    month_by = fields.Selection([
        ('date', 'Date of month'),
        ('day', 'Day of month')
    ], string='Option', default='date', oldname='select1')
    day = fields.Integer('Date of month', default=1)
    week_list = fields.Selection([
        ('MO', 'Monday'),
        ('TU', 'Tuesday'),
        ('WE', 'Wednesday'),
        ('TH', 'Thursday'),
        ('FR', 'Friday'),
        ('SA', 'Saturday'),
        ('SU', 'Sunday')
    ], string='Weekday')
    byday = fields.Selection([
        ('1', 'First'),
        ('2', 'Second'),
        ('3', 'Third'),
        ('4', 'Fourth'),
        ('5', 'Fifth'),
        ('-1', 'Last')
    ], string='By day')
    final_date = fields.Date('Repeat Until')

    @api.depends('byday', 'recurrency', 'final_date', 'rrule_type', 'month_by', 'interval', 'count', 'end_type', 'mo', 'tu', 'we', 'th', 'fr', 'sa', 'su', 'day', 'week_list')
    def _compute_rrule(self):
        """ Gets Recurrence rule string according to value type RECUR of iCalendar from the values given.
            :return dictionary of rrule value.
        """
        for meeting in self:
            if meeting.recurrency:
                meeting.rrule = meeting._rrule_serialize()
            else:
                meeting.rrule = ''

    @api.multi
    def _inverse_rrule(self):
        for meeting in self:
            if meeting.rrule:
                data = self._rrule_default_values()
                data['recurrency'] = True
                data.update(self._rrule_parse(meeting.rrule, data, meeting.start))
                meeting.update(data)

    @api.constrains('start_datetime', 'stop_datetime')
    def _check_closing_date(self):
            if self.start_datetime and self.stop_datetime and self.stop_datetime < self.start_datetime:
                raise ValidationError(_('Ending datetime cannot be set before starting datetime.'))
    
    def _rrule_default_values(self):
        return {
            'byday': False,
            'recurrency': False,
            'final_date': False,
            'rrule_type': False,
            'month_by': False,
            'interval': 0,
            'count': False,
            'end_type': False,
            'mo': False,
            'tu': False,
            'we': False,
            'th': False,
            'fr': False,
            'sa': False,
            'su': False,
            'day': False,
            'week_list': False
        }

    def _rrule_parse(self, rule_str, data, date_start):
        day_list = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
        rrule_type = ['yearly', 'monthly', 'weekly', 'daily']
        ddate = fields.Datetime.from_string(date_start)
        if 'Z' in rule_str and not ddate.tzinfo:
            ddate = ddate.replace(tzinfo=pytz.timezone('UTC'))
            rule = rrule.rrulestr(rule_str, dtstart=ddate)
        else:
            rule = rrule.rrulestr(rule_str, dtstart=ddate)

        if rule._freq > 0 and rule._freq < 4:
            data['rrule_type'] = rrule_type[rule._freq]
        data['count'] = rule._count
        data['interval'] = rule._interval
        data['final_date'] = rule._until and rule._until.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        #repeat weekly
        if rule._byweekday:
            for i in range(0, 7):
                if i in rule._byweekday:
                    data[day_list[i]] = True
            data['rrule_type'] = 'weekly'
        #repeat monthly by nweekday ((weekday, weeknumber), )
        if rule._bynweekday:
            data['week_list'] = day_list[list(rule._bynweekday)[0][0]].upper()
            data['byday'] = str(list(rule._bynweekday)[0][1])
            data['month_by'] = 'day'
            data['rrule_type'] = 'monthly'

        if rule._bymonthday:
            data['day'] = list(rule._bymonthday)[0]
            data['month_by'] = 'date'
            data['rrule_type'] = 'monthly'

        #repeat yearly but for odoo it's monthly, take same information as monthly but interval is 12 times
        if rule._bymonth:
            data['interval'] = data['interval'] * 12

        #FIXEME handle forever case
        #end of recurrence
        #in case of repeat for ever that we do not support right now
        if not (data.get('count') or data.get('final_date')):
            data['count'] = 100
        if data.get('count'):
            data['end_type'] = 'count'
        else:
            data['end_type'] = 'end_date'
        return data

    @api.multi
    def _rrule_serialize(self):
        """ Compute rule string according to value type RECUR of iCalendar
            :return: string containing recurring rule (empty if no rule)
        """
        if self.interval and self.interval < 0:
            raise UserError(_('interval cannot be negative.'))
        if self.count and self.count <= 0:
            raise UserError(_('Event recurrence interval cannot be negative.'))

        def get_week_string(freq):
            weekdays = ['mo', 'tu', 'we', 'th', 'fr', 'sa', 'su']
            if freq == 'weekly':
                byday = [field.upper() for field in weekdays if self[field]]
                if byday:
                    return ';BYDAY=' + ','.join(byday)
            return ''

    def set_events_to_ocd(self):

        partner_ocd_ids = self.env['hr.employee'].search(
            [('job_id', 'in', self.job_ids.ids)]).mapped('user_id.partner_id.id')
        lines1 = [(4, id, 0) for id in partner_ocd_ids]
        vals = {
            'principal': self.principal,
            'name': self.acronym,
            'start': self.start_datetime,
            'stop': self.stop_datetime,
            'location':self.location,
            'byday': self.byday,
            'recurrency': self.recurrency,
            'final_date': self.final_date,
            'rrule_type': self.rrule_type,
            'month_by': self.month_by,
            'interval': self.interval,
            'count': self.count,
            'end_type': self.end_type,
            'mo': self.mo,
            'tu': self.tu,
            'we': self.we,
            'th': self.we,
            'fr': self.fr,
            'sa': self.sa,
            'su': self.su,
            'day': self.day,
            'week_list': self.week_list,
            'partner_ids': lines1,   
            'ocd': self.id,
        }
        self.env['calendar.event'].create(vals)
        self.ocd_flag = self.env['calendar.event'].search_count([('ocd', '=', self.id)])
    
    @api.multi
    def write(self, vals):
        ocd_write = super(OCD,self).write(vals)

        ocd_event = self.env['calendar.event'].search([('ocd', '=', self.id)])

        partner_ocd_ids = self.env['hr.employee'].search(
            [('job_id', 'in', self.job_ids.ids)]).mapped('user_id.partner_id.id')
        _logger.info(partner_ocd_ids)

        lines1 = [(6, 0, partner_ocd_ids)]
        val = {
            'principal': self.principal,
            'name': self.acronym,
            'start': self.start_datetime,
            'stop': self.stop_datetime,
            'location':self.location,
            'byday': self.byday,
            'recurrency': self.recurrency,
            'final_date': self.final_date,
            'rrule_type': self.rrule_type,
            'month_by': self.month_by,
            'interval': self.interval,
            'count': self.count,
            'end_type': self.end_type,
            'mo': self.mo,
            'tu': self.tu,
            'we': self.we,
            'th': self.we,
            'fr': self.fr,
            'sa': self.sa,
            'su': self.su,
            'day': self.day,
            'week_list': self.week_list,
            'partner_ids': lines1,          
        }

        ocd_event.write(val)

        return True
    
    @api.multi
    def unlink(self):
        ocd_event = self.env['calendar.event'].search([('ocd', '=', self.id)])
        ocd_event.unlink()
        res = super(OCD,self).unlink()
        
        return True
    


