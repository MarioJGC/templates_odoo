# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import re
from collections import defaultdict
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import is_html_empty, remove_accents

# see rfc5322 section 3.2.3
atext = r"[a-zA-Z0-9!#$%&'*+\-/=?^_`{|}~]"
dot_atom_text = re.compile(r"^%s+(\.%s+)*$" % (atext, atext))


class Alias(models.Model):
    _inherit = 'mail.alias'
    
    #originalmente la pk estaba formada por el alias_name y el domain_id, por ejemplo solo podia haber un registr
    #de correo1@gmail.com en los seudonimos y eso era gracias a esa pk nativa, pero como necesito que varios
    #registros de equipos de leads tengan el mismo seudonimo, debo de crear un registro correo1@gmail.com
    #para cada equipo distinto, entonces en seudonimos pareciera que hubieran registros repetidos, pero cada
    #uno esta asociado a un equipo distinto
    def init(self):
        #asi que primeramente elimino ese index nativo formado por el alias_name y alias_domain_id
        self.env.cr.execute("""
            DROP INDEX IF EXISTS mail_alias_name_domain_unique;
        """)
        #y para no complicarmela reemplace el alias_name por el id, asi tambien me aseguro que la pk será unica
        #ya que el id es siempre incremental y distinto para todos los registros
        self.env.cr.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS mail_alias_id_domain_unique
            ON mail_alias (id, COALESCE(alias_domain_id, 0));
        """)
    
    #aca me copie este metodo ya que para lograr lo que quiero de que cada equipo de lead tenga el mismo seudonimo
    #debo de hacer que no me interfiera la validacion nativa
    def _check_unique(self, alias_names, alias_domains):
        """ Check unicity constraint won't be raised, otherwise raise a UserError
        with a complete error message. Also check unicity against alias config
        parameters.

        :param list alias_names: a list of names (considered as sanitized
          and ready to be sent to DB);
        :param list alias_domains: list of alias_domain records under which
          the check is performed, as uniqueness is performed for given pair
          (name, alias_domain);
        """
        if len(alias_names) != len(alias_domains):
            msg = (f"Invalid call to '_check_unique': names and domains should make coherent lists, "
                   f"received {', '.join(alias_names)} and {', '.join(alias_domains.mapped('name'))}")
            raise ValueError(msg)

        # reorder per alias domain, keep only not void alias names (void domain also checks uniqueness)
        domain_to_names = defaultdict(list)
        for alias_name, alias_domain in zip(alias_names, alias_domains):
            if alias_name and alias_name in domain_to_names[alias_domain]:
                raise UserError(
                    _('Email aliases %(alias_name)s cannot be used on several records at the same time. Please update records one by one.',
                      alias_name=alias_name)
                )
            if alias_name:
                domain_to_names[alias_domain].append(alias_name)

        # matches existing alias
        domain = expression.OR([
            ['&', ('alias_name', 'in', alias_names), ('alias_domain_id', '=', alias_domain.id)]
            for alias_domain, alias_names in domain_to_names.items()
        ])
        if domain and self:
            domain = expression.AND([domain, [('id', 'not in', self.ids)]])
        existing = self.search(domain, limit=1) if domain else self.env['mail.alias']
        if not existing:
            return
        if existing.alias_parent_model_id and existing.alias_parent_thread_id:
            #aca es cuando retorno para que no salte esta validacion nativa si es que se repite el seudonimo
            return
            parent_name = self.env[existing.alias_parent_model_id.model].sudo().browse(existing.alias_parent_thread_id).display_name
            msg_begin = _(
                'Alias %(matching_name)s (%(current_id)s) is already linked with %(alias_model_name)s (%(matching_id)s) and used by the %(parent_name)s %(parent_model_name)s.',
                alias_model_name=existing.alias_model_id.name,
                current_id=self.ids if self else _('your alias'),
                matching_id=existing.id,
                matching_name=existing.display_name,
                parent_name=parent_name,
                parent_model_name=existing.alias_parent_model_id.name
            )
        else:
            msg_begin = _(
                'Alias %(matching_name)s (%(current_id)s) is already linked with %(alias_model_name)s (%(matching_id)s).',
                alias_model_name=existing.alias_model_id.name,
                current_id=self.ids if self else _('new'),
                matching_id=existing.id,
                matching_name=existing.display_name,
            )
        msg_end = _('Choose another value or change it on the other document.')
        raise UserError(f'{msg_begin} {msg_end}')
