# -*- encoding: utf-8 -*-
from odoo import models, fields, api


class AttendeesWizard(models.TransientModel):
    _name = 'attendees_department.wizard'
    _description = 'Events Mass Assignment'
    event_ids = fields.Many2many('calendar.event', domain=lambda self: [('user_id', '=', self.env.user.id)], string= 'Events')
    department_ids = fields.Many2many('hr.department', string='Departments')

    @api.multi
    def set_events_to_department(self):
        self.ensure_one()

        partner_department_ids = self.env['hr.employee'].search([
            ('department_id', 'in', self.department_ids.ids)]).mapped('user_id.partner_id.id')
        lines = [(4, id, 0) for id in partner_department_ids]
        self.event_ids.write({
            'partner_ids': lines
        })
