# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#################################################################################
from odoo import http
from odoo.http import request
from odoo.tools.translate import _
import werkzeug.utils
import hashlib
from odoo import http
from odoo.http import request
import json
import simplejson
from odoo.addons.web.controllers.main import Home, ensure_db
from odoo.addons.bus.controllers.main import BusController

import logging

_logger = logging.getLogger(__name__)

class Home(Home):
    @http.route('/web/login', type='http', auth="none", sitemap=False)
    def web_login(self, redirect=None, **kw):
        res = super(Home, self).web_login(redirect, **kw)
        if request.params['login_success']:
            uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
            users = request.env['res.users'].browse([uid])
            if users.login_with_pos_screen:
                pos_session = request.env['pos.session'].sudo().search(
                    [('config_id', '=', users.default_pos.id), ('state', '=', 'opened')])
                if pos_session:
                    return http.redirect_with_hash('/pos/web')
                else:
                    session_id = users.default_pos.open_session_cb()
                    pos_session = request.env['pos.session'].sudo().search(
                        [('config_id', '=', users.default_pos.id), ('state', '=', 'opening_control')])
                    if users.default_pos.cash_control:
                        pos_session.write({'opening_balance': True})
                    session_open = pos_session.action_pos_session_open()
                    return http.redirect_with_hash('/pos/web')
            else:
                return res
        else:
            return res

class DataSet(http.Controller):

    @http.route('/web/dataset/get_country', type='http', auth="user")
    def get_country(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        county_code = kw.get('country_code')
        country_obj = request.env['res.country']
        country_id = country_obj.search([('code','=',county_code)])
        if country_id:
            data = country_id.read()
            data[0]['image'] = False 
            return json.dumps(data)
        else:
            return False


    @http.route('/web/dataset/send_pos_ordermail', type='http', auth="user")
    def send_pos_ordermail(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        order_ids = eval(kw.get('order_ids'))
        orders = request.env['pos.order'].browse(order_ids)
        for order in orders:
            if order.reserved and order.session_id.config_id.enable_pos_welcome_mail:
                try:
                    template_id = request.env['ir.model.data'].get_object_reference('flexiretail_com_advance', 'email_template_pos_ereceipt_reservation')
                    template_obj = request.env['mail.template'].browse(template_id[1])
                    template_obj.send_mail(order.id,force_send=True, raise_exception=True)
                except Exception as e:
                    _logger.error('Unable to send email for order %s', e)
            if order.partner_id.email and order.session_id.config_id.enable_ereceipt and not order.reserved:
                try:
                    template_id = request.env['ir.model.data'].get_object_reference('flexiretail_com_advance', 'email_template_pos_ereceipt')
                    template_obj = request.env['mail.template'].browse(template_id[1])
                    template_obj.send_mail(order.id,force_send=True, raise_exception=True,email_values={'email_to':order.partner_id.email})
                except Exception as e:
                    _logger.error('Unable to send email for order %s',e)
        return json.dumps([])


    #load background
    @http.route('/web/dataset/load_products', type='http', auth="user")
    def load_products(self, **kw):
        cr, uid, context = request.cr, request.uid, request.context
        product_ids = eval(kw.get('product_ids'))
        fields = eval(kw.get('fields'))
        if product_ids and fields:
            records = request.env['product.product'].search_read([('id','in',product_ids)], fields)
            if records:
                return simplejson.dumps(records)
        return json.dumps([])
#     @http.route('/web/dataset/load_products', type='http', auth="user")
#     def load_products(self, **kw):
#         cr, uid, context = request.cr, request.uid, request.context
#         product_ids = eval(kw.get('product_ids'))
#         fields = eval(kw.get('fields'))
#         ctx1 = str(kw.get('context'))
#         ctx1 = ctx1.replace('true', 'True')
#         ctx1 = ctx1.replace('false', 'False')
#         ctx1 = eval(ctx1)
#         fields = eval(kw.get('fields'))
#         cr, uid, context = request.cr, request.uid, request.context
#         context = dict(context)
#         context.update(ctx1)
#         if product_ids and fields:
#             records = request.env['product.product'].with_context(context).search_read([('id','in',product_ids)], fields)
#             if records:
#                 return json.dumps(records)
#         return json.dumps([])


class TerminalLockController(BusController):

    def _poll(self, dbname, channels, last, options):
        """Add the relevant channels to the BusController polling."""
        if options.get('customer.display'):
            channels = list(channels)
            ticket_channel = (
                request.db,
                'customer.display',
                options.get('customer.display')
            )
            channels.append(ticket_channel)
        if options.get('lock.data'):
            channels = list(channels)
            lock_channel = (
                request.db,
                'lock.data',
                options.get('lock.data')
            )
            channels.append(lock_channel)
        if options.get('sale.note'):
            channels = list(channels)
            lock_channel = (
                request.db,
                'sale.note',
                options.get('sale.note')
            )
            channels.append(lock_channel)
        if options.get('change_detector'):
            channels = list(channels)
            channels.append((request.db, 'change_detector'))

        return super(TerminalLockController, self)._poll(dbname, channels, last, options)


class PosMirrorController(http.Controller):
 
    @http.route('/web/customer_display', type='http', auth='user')
    def white_board_web(self, **k):
        config_id = False
        pos_sessions = request.env['pos.session'].search([
            ('state', '=', 'opened'),
            ('user_id', '=', request.session.uid),
            ('rescue', '=', False)])
        if pos_sessions:
            config_id = pos_sessions.config_id.id
        context = {
            'session_info': json.dumps(request.env['ir.http'].session_info()),
            'config_id': config_id,
        }
        return request.render('flexiretail_com_advance.customer_display_index', qcontext=context)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: