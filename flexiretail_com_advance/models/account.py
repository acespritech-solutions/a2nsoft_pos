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

from odoo import models, api, fields, _
from datetime import datetime

class account_journal(models.Model):
    _inherit="account.journal"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('config_jr'):
            if self._context.get('journal_ids') and \
               self._context.get('journal_ids')[0] and \
               self._context.get('journal_ids')[0][2]:
               args += [['id', 'in', self._context.get('journal_ids')[0][2]]]
            else:
                return False;
        return super(account_journal, self).name_search(name, args=args, operator=operator, limit=limit)

    shortcut_key = fields.Char('Shortcut Key')
    jr_use_for = fields.Selection([
        ('loyalty', "Loyalty"),
        ('gift_card', "Gift Card"),
        ('gift_voucher', "Gift Voucher"),
        ('rounding', "Rounding"),
        ('credit',"Credit")
    ], string="Method Use For",
        help='This payment method reserve for particular feature, that accounting entry will manage based on assigned features.')
    apply_charges = fields.Boolean("Apply Charges");
    fees_amount = fields.Float("Fees Amount");
    fees_type = fields.Selection(selection=[('fixed','Fixed'),('percentage','Percentage')],string="Fees type", default="fixed")
    optional = fields.Boolean("Optional")

class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"
 
    @api.one
    @api.constrains('amount')
    def _check_amount(self):
        if not self._context.get('from_pos'):
            super(AccountBankStatementLine, self)._check_amount()

    @api.one
    @api.constrains('amount', 'amount_currency')
    def _check_amount_currency(self):
        if not self._context.get('from_pos'):
            super(AccountBankStatementLine, self)._check_amount_currency()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
