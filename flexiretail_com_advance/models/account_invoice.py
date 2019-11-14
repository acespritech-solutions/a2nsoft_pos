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

from odoo import fields,api,models,_
from odoo.tools import float_is_zero, float_compare, pycompat


class InvoiceInfo(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def get_outstanding_info(self,vals):
        if(vals):
            partner_id = self.env['res.partner'].browse(vals);
            account_id = partner_id.property_account_receivable_id
            comp_id = self.env['res.partner']._find_accounting_partner(partner_id).id;
            domain = [('account_id', '=', account_id.id),
                      ('partner_id', '=',  self.env['res.partner']._find_accounting_partner(partner_id).id),
                      ('reconciled', '=', False), '|', ('amount_residual', '!=', 0.0),
                      ('amount_residual_currency', '!=', 0.0)]
            domain.extend([('credit', '>', 0), ('debit', '=', 0)])
            type_payment = _('Outstanding credits')
            lines = self.env['account.move.line'].search(domain)
            info = {'title': '', 'outstanding': True, 'content': [], 'invoice_id': self.id}
            if len(lines) != 0:
                for line in lines:
                    if line.currency_id and line.currency_id == self.currency_id:
                        amount_to_show = abs(line.amount_residual_currency)
                    else:
                        amount_to_show = line.company_id.currency_id.with_context(date=line.date).compute(abs(line.amount_residual), self.currency_id)
                    if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                        continue
                    info['content'].append({
                        'journal_name': line.ref or line.move_id.name,
                        'amount': amount_to_show,
                        'id': line.id,
                    })
                info['title'] = type_payment
        return info

    @api.model
    def get_credit_info(self,vals):
        lines_info = []
        move_line_obj = self.env['account.move.line']
        if vals:
            for each in vals:
                if each['partner_id']:
                    partner_id = self.env['res.partner'].browse(each['partner_id']);
                credit_aml = self.env['account.move.line'].browse(each['journal_id'])
                move_line_obj |= credit_aml
                credit_journal_id = credit_aml.journal_id.default_credit_account_id
                debit_account_id = credit_aml.journal_id.default_debit_account_id
                account_id = partner_id.property_account_receivable_id
                lines_info.append((0, 0, {'account_id': account_id.id,
                                           'debit': each['amount'],
                                           'partner_id': partner_id.id,
                                      }))
                lines_info.append((0, 0, {'account_id': credit_journal_id.id,
                                      'credit': each['amount'],
                                      'partner_id': partner_id.id,
                                      }))

                move = self.env['account.move'].create({'ref':'',
                                                    'journal_id':credit_aml.payment_id.journal_id.id,
                                                    'line_ids':lines_info,
                                                    })
                lines_info = []
                line_id = move.line_ids.filtered(lambda l:l.account_id.id==account_id.id and l.partner_id.id == partner_id.id)
                self.env['account.partial.reconcile'].create(
                    {'credit_move_id': credit_aml.id, 'debit_move_id': line_id.id,
                     'amount': line_id.debit,
                     })
                move.post()
        return True

#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
