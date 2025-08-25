from odoo import models, fields, api
import ast

class MailActivitySchedule(models.TransientModel):
    _inherit = 'mail.activity.schedule'
    
    template_id = fields.Many2one('mail.template', string='Use template')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'mail_compose_message_attachments_rel',
        'wizard_id', 'attachment_id', string='Attachments',
        readonly=False, store=True)
    start_date = fields.Date(default=fields.Date.today())

    note = fields.Html('Note', sanitize_style=True, compute='_compute_body', readonly=False, store=True, render_engine='qweb', render_options={'post_process': True})

    type_lead = fields.Char(
        string='Tipo de Pipeline',
        help='Este es un campo donde se obtendra tipo de pipeline del lead.',
        compute='_compute_type_lead'
    )

    activity_user_ids = fields.Many2many(
        'res.partner',
        'mail_message_activity_user_rel',
        'wizard_id',
        'user_id',
        string='Destinatarios',
        readonly=False,
        store=True,)

    @api.model
    def default_get(self, vals):
        res = super(MailActivitySchedule, self).default_get(vals)

        model = res.get('res_model') 
        res_ids = res.get('res_ids')

        res_ids = ast.literal_eval(res_ids)

        if model and res_ids:
            record = self.env[model].browse(res_ids) # Aqui aparece el error

            if record.exists():
                follower_ids = record.message_partner_ids.ids
                current_user_partner_id = self.env.user.partner_id.id

                follower_ids = [fid for fid in follower_ids if fid != current_user_partner_id]

                if follower_ids:
                    res['activity_user_ids'] = [(6, 0, follower_ids)]

        return res

    @api.onchange('attachment_ids')
    def convert_attachments_to_binary(self):
        for activity in self:
            for attachment in activity.attachment_ids:
                if attachment.type != 'binary':
                    attachment.write({'type': 'binary'})

    def _action_schedule_activities(self):
        """ Extiende el método para incluir los nuevos campos en `mail.activity` """
        activities = self._get_applied_on_records().activity_schedule(
            activity_type_id=self.activity_type_id.id,
            automated=False,
            summary=self.summary,
            note=self.note,
            user_id=self.activity_user_id.id,
            date_deadline=self.date_deadline
        )
        
        # Actualizar actividades con los nuevos valores
        for activity in activities:
            activity.write({
                'activity_user_ids' : self.activity_user_ids,
                'template_id': self.template_id.id,
                'attachment_ids': [(6, 0, self.attachment_ids.ids)],
                'start_date': self.start_date,
            })

            if self.type_lead == 'privadas':

                model_id = self.env['ir.model'].search([('model', '=', 'crm.team')], limit=1).id

                # Obteniendo el seudónimo de crm
                alias = self.env['mail.alias'].search([
                    ('alias_parent_model_id', '=', model_id)
                ], limit=1)

                message = self.env['mail.message'].create({
                    'model': activity.res_model,  
                    'res_id': activity.res_id,  
                    'body': activity.note,  
                    'subject': activity.summary,  
                    'message_type': 'email_outgoing',  
                    'author_id': self.env.user.partner_id.id,  
                    'partner_ids': [(6, 0, self.activity_user_ids.ids)],  
                    'attachment_ids': [(6, 0, self.attachment_ids.ids)],  
                    'reply_to': alias.alias_full_name,
                    'subtype_id': self.env.ref('mail.mt_comment').id  
                })

                # Enviar correo electronico
                mail_values = {
                    'subject': activity.summary,
                    'body_html': activity.note,
                    'email_to': ','.join(activity.activity_user_ids.mapped('email')),
                    'email_from': self.env.user.partner_id.email,
                    'reply_to': alias.alias_full_name,
                    'attachment_ids': [(6, 0, self.attachment_ids.ids)],
                    'mail_message_id': message.id
                }

                # Solo enviamos si hay destinatarios
                if mail_values['email_to'] and mail_values['email_from']:
                    mail = self.env['mail.mail'].create(mail_values)
                    mail.send()

        return activities

    @api.depends('template_id')
    def _compute_body(self):

        for activity_schedule in self:
            if activity_schedule.template_id:
                activity_schedule.summary = activity_schedule.template_id.subject
                activity_schedule.note = activity_schedule.template_id.body_html

            if not activity_schedule.template_id:
                activity_schedule.summary = False
                activity_schedule.note = False
    
    @api.depends('res_model')
    def _compute_type_lead(self):
        for activity in self:
            if activity.res_model == 'crm.lead' and activity.res_ids:
                id_model = activity.res_ids
                lead_id = int(id_model.strip('[]'))
                lead = activity.env['crm.lead'].browse(lead_id)

                # El campo type_pipeline_text se crea en los leads por defecto en el módulo 'dv_crm_filter_template_custom'
                if lead.type_pipeline_text:
                    activity.type_lead = lead.type_pipeline_text.lower()
                else:
                    activity.type_lead = False
            else:
                activity.type_lead = False