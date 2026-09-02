# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.tools import formatLang

WARNING_THRESHOLD = 0.8
DANGER_THRESHOLD = 1.0


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    credit_limit_warning_level = fields.Selection(
        [
            ('none', 'None'),
            ('warning', 'Warning'),
            ('danger', 'Danger'),
        ],
        string='Credit Limit Warning Level',
        compute='_compute_credit_limit_warning',
        store=False,
    )
    credit_limit_warning_message = fields.Text(
        string='Credit Limit Warning Message',
        compute='_compute_credit_limit_warning',
        store=False,
    )

    @api.depends(
        'partner_id', 'order_line.price_total', 'amount_total', 'company_id', 'state',
    )
    def _compute_credit_limit_warning(self):
        for order in self:
            order.credit_limit_warning_level = 'none'
            order.credit_limit_warning_message = False

            if order.state not in ('draft', 'sent') or not order.company_id.account_use_credit_limit:
                continue

            partner = order.partner_id.sudo().commercial_partner_id
            credit_limit = partner.credit_limit
            if not credit_limit:
                continue

            order_sudo = order.sudo()
            current_amount = order_sudo.amount_total / order_sudo.currency_rate
            outstanding = partner.credit + partner.credit_to_invoice
            total_exposure = outstanding + current_amount
            ratio = total_exposure / credit_limit

            if ratio >= DANGER_THRESHOLD:
                level = 'danger'
            elif ratio >= WARNING_THRESHOLD:
                level = 'warning'
            else:
                level = 'none'

            order.credit_limit_warning_level = level
            if level == 'none':
                continue

            currency = order.company_id.currency_id
            order.credit_limit_warning_message = "\n".join([
                _(
                    '%(partner_name)s has a credit limit of %(credit_limit)s.',
                    partner_name=partner.name,
                    credit_limit=formatLang(order.env, credit_limit, currency_obj=currency),
                ),
                _(
                    'Current outstanding balance (posted and to invoice): %(outstanding)s.',
                    outstanding=formatLang(order.env, outstanding, currency_obj=currency),
                ),
                _(
                    'This order would add: %(order_amount)s.',
                    order_amount=formatLang(order.env, current_amount, currency_obj=currency),
                ),
            ])
