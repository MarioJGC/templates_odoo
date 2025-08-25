from odoo import models, fields, api
import ast

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    template_id = fields.Many2one('mail.template', string='Use template')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'mail_activity_attachments_rel',
        'activity_id', 'attachment_id', string='Attachments')

    activity_user_ids = fields.Many2many(
        'res.partner',
        'mail_message_activity_partner_rel',
        'wizard_id',
        'user_id',
        string='Destinatarios',
        readonly=False,
        store=True,)

    start_date = fields.Date()

    note = fields.Html('Note', sanitize_style=True, compute='_compute_body', readonly=False, store=True, render_engine='qweb', render_options={'post_process': True})

    type_lead = fields.Char(
        string='Tipo de Pipeline',
        help='Este es un campo donde se obtendra tipo de pipeline del lead.',
        compute='_compute_type_lead'
    )

    @api.onchange('template_id')
    def _compute_body(self):
        for activity_schedule in self:
            if activity_schedule.template_id:
                activity_schedule.summary = activity_schedule.template_id.subject
                activity_schedule.note = activity_schedule.template_id.body_html

            if not activity_schedule.template_id:
                activity_schedule.summary = False
                activity_schedule.note = False

    def action_close_dialog(self):
        res = super().action_close_dialog()

        # Cracion de mail.message y mail
        if self.type_lead == 'privadas':
            model_id = self.env['ir.model'].search([('model', '=', 'crm.team')], limit=1).id

            # Obteniendo el seudónimo de crm
            alias = self.env['mail.alias'].search([
                ('alias_parent_model_id', '=', model_id)
            ], limit=1)

            message = self.env['mail.message'].create({
                'model': self.res_model,  
                'res_id': self.res_id,  
                'body': self.note,  
                'subject': self.summary,  
                'message_type': 'email_outgoing',  
                'author_id': self.env.user.partner_id.id,  
                'partner_ids': [(6, 0, self.activity_user_ids.ids)],  
                'attachment_ids': [(6, 0, self.attachment_ids.ids)],  
                'reply_to': alias.alias_full_name,
                'subtype_id': self.env.ref('mail.mt_comment').id  
            })

            # Enviar correo electronico
            mail_values = {
                'subject': self.summary,
                'body_html': self.note,
                'email_to': ','.join(self.activity_user_ids.mapped('email')),
                'email_from': self.env.user.partner_id.email,
                'reply_to': alias.alias_full_name,
                'attachment_ids': [(6, 0, self.attachment_ids.ids)],
                'mail_message_id': message.id
            }

            # Solo enviamos si hay destinatarios
            if mail_values['email_to'] and mail_values['email_from']:
                mail = self.env['mail.mail'].create(mail_values)
                mail.send()

        return res

    @api.depends('res_model')
    def _compute_type_lead(self):
        for activity in self:
            if activity.res_model == 'crm.lead' and activity.res_id:
                id_model = activity.res_id
                lead_id = int(id_model)
                lead = activity.env['crm.lead'].browse(lead_id)

                # El campo type_pipeline_text se crea en los leads por defecto en el módulo 'dv_crm_filter_template_custom'
                if lead.type_pipeline_text:
                    activity.type_lead = lead.type_pipeline_text.lower()
                else:
                    activity.type_lead = False
            else:
                activity.type_lead = False