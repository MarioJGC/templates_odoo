from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = "stock.move"
    
    is_change_uom = fields.Boolean(string='Is Change UOM', compute='_compute_is_change_uom', store=True)
    
    @api.depends('product_uom', 'quantity')
    def _compute_is_change_uom(self):
        for record in self:
            if record.product_id.pack_product_ids and record.picking_id:
                for move in record.picking_id.move_ids_without_package:
                    if move.product_tmpl_id in record.product_id.pack_product_ids:
                        quantity = record.quantity * move.product_uom.ratio
                        for move_line in move.move_line_ids:
                            previous_state = move_line.state
                            move_line.state = 'draft'
                            move_line.update({
                                'product_uom_id': move.product_uom.id,
                                'quantity': quantity,
                            })
                            move_line.state = previous_state
                            break
                        move.write({
                            'quantity': quantity,
                        })
            if record.picking_id and not record.product_id.pack_product_ids:
                for move in record.picking_id.move_ids_without_package:
                    if move.product_id.pack_product_ids:
                        if record.product_tmpl_id in move.product_id.pack_product_ids:
                            quantity = move.quantity * record.product_uom.ratio
                            for move_line in record.move_line_ids:
                                previous_state = move_line.state
                                move_line.state = 'draft'
                                move_line.update({
                                    'product_uom_id': record.product_uom.id,
                                    'quantity': quantity,
                                })
                                move_line.state = previous_state
                                break
                            record.write({
                                'quantity': quantity,
                            })
                            break
            if not record.is_change_uom:
                record.is_change_uom = True
            else:
                record.is_change_uom = False        
    # @api.onchange('product_uom')
    # def onchange_quantity_for_udm(self):
    #     for record in self:
    #         if record.picking_id:
    #             #verifica si hay pack en los movimientos del picking
    #             for move in record.picking_id.move_ids_without_package:
    #                 if move.product_id.pack_product_ids:
    #                     if record.product_tmpl_id in move.product_id.pack_product_ids:
    #                         quantity = move.quantity * record.product_uom.ratio
    #                         for move_line in record.move_line_ids:
    #                             previous_state = move_line.state
    #                             move_line.state = 'draft'
    #                             move_line.update({
    #                                 'product_uom_id': record.product_uom.id,
    #                                 'quantity': quantity,
    #                             })
    #                             move_line.state = previous_state
    #                             break
    #                         record.quantity = quantity
    #                         break
                        
    # @api.model
    # def write(self, vals):
    #     res = super(StockMove, self).write(vals)
    #     # Lógica para actualizar los movimientos después de guardar
    #     for record in self:
    #         if 'quantity' in vals and record.product_id.pack_product_ids and record.picking_id:
    #             for move in record.picking_id.move_ids_without_package:
    #                 if move.product_tmpl_id in record.product_id.pack_product_ids:
    #                     quantity = record.quantity * move.product_uom.ratio
    #                     for move_line in move.move_line_ids:
    #                         previous_state = move_line.state
    #                         move_line.state = 'draft'
    #                         move_line.update({
    #                             'product_uom_id': move.product_uom.id,
    #                             'quantity': quantity,
    #                         })
    #                         move_line.state = previous_state
    #                         break
    #                     move.quantity = quantity
    #         if 'product_uom' in vals and record.picking_id:
    #             for move in record.picking_id.move_ids_without_package:
    #                 if move.product_id.pack_product_ids:
    #                     if record.product_tmpl_id in move.product_id.pack_product_ids:
    #                         quantity = move.quantity * record.product_uom.ratio
    #                         for move_line in record.move_line_ids:
    #                             previous_state = move_line.state
    #                             move_line.state = 'draft'
    #                             move_line.update({
    #                                 'product_uom_id': record.product_uom.id,
    #                                 'quantity': quantity,
    #                             })
    #                             move_line.state = previous_state
    #                             break
    #                         record.quantity = quantity
    #                         break           
    #     return res

    def _split(self, qty, restrict_partner_id=False):
        res = super(StockMove, self)._split(qty, restrict_partner_id)
        for record in self:
            if record.picking_id:
                for move in record.picking_id.move_ids_without_package:
                    if move.product_id.pack_product_ids:
                        init_qty = 0
                        if record.product_tmpl_id in move.product_id.pack_product_ids:
                            order_id = move.picking_id.sale_id
                            for line in order_id.order_line:
                                if line.product_id == move.product_id:
                                    init_qty = line.product_uom_qty
                            difference = abs(init_qty - move.quantity)
                            for move_vals in res:
                                if 'product_uom_qty' in move_vals:
                                    move_vals['product_uom_qty'] = difference * record.product_uom.ratio
        return res