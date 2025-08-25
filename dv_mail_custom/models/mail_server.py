from odoo import models, fields, api
from odoo.exceptions import ValidationError

class MailServer(models.Model):
    _inherit = "ir.mail_server"

    #metodo que se ejecuta al presionar el boton de la vista lista
    @api.model
    def create_servers_for_users_from_selected(self):
        #obtengo los registros seleccionados
        selected_servers = self.env.context.get('active_ids')
        if not selected_servers:
            raise ValueError("No se seleccionó ningún servidor de correo")
        if len(selected_servers) > 1:
            raise ValidationError("Solo se puede seleccionar un servidor de correo para copiar")
        
        #busco los grupos
        allowed_groups = [
            self.env.ref("dv_access_groups.group_crm_admin").id,
            self.env.ref("dv_access_groups.group_crm_comercial").id
        ]
        #recorrer el servidor seleccionado
        for mail_server in self.browse(selected_servers):
            #solo usuarios con email y pertenecientes a esos grupos
            users = self.env['res.users'].search([
                ('email', '!=', False),
                ('groups_id', 'in', allowed_groups)
            ])
            
            for user in users:
                #verifico si ya existe un servidor de correo para este usuario
                existing_server = self.env['ir.mail_server'].search([('smtp_user', '=', user.email)])
                if existing_server:
                    continue  # Saltar si ya existe

                #copia del servidor seleccionado
                mail_server.copy({
                    'name': f"Correo saliente para {user.name}",
                    'smtp_user': user.email,
                    'smtp_pass': '',  #contraseña vacia para ajuste manual
                    'sequence': 10,   
                    'smtp_authentication': mail_server.smtp_authentication,
                    'from_filter': user.email
                })

        #retorno accion para recargar la vista actual
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
