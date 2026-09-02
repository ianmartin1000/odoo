# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tools import formatLang

from odoo.addons.sale.tests.common import SaleCommon


@tagged('post_install', '-at_install')
class TestSaleOrderCreditLimitWarning(SaleCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 'credit_to_invoice' (confirmed-but-not-yet-invoiced) is only populated
        # when the company has the credit-limit feature enabled — mirrors the
        # setup convention in addons/sale/tests/test_credit_limit.py.
        cls.env.company.account_use_credit_limit = True
        cls.customer = cls.env['res.partner'].create({'name': 'Credit Warning Customer'})

    def _create_order(self, amount, partner=None):
        partner = partner or self.customer
        return self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': 1,
                'price_unit': amount,
                'tax_id': False,
            })],
        })

    def _build_outstanding(self, credit_to_invoice=0.0, credit=0.0):
        """Build up partner.credit / partner.credit_to_invoice via a confirmed
        (not yet invoiced) sale order and a posted customer invoice, mirroring
        the setup conventions in addons/sale/tests/test_credit_limit.py."""
        if credit_to_invoice:
            confirmed_order = self._create_order(credit_to_invoice)
            confirmed_order.action_confirm()
        if credit:
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.customer.id,
                'invoice_line_ids': [Command.create({
                    'name': 'Outstanding balance seed',
                    'quantity': 1,
                    'price_unit': credit,
                    'tax_ids': False,
                })],
            })
            invoice.action_post()
        self.customer.invalidate_recordset(['credit', 'credit_to_invoice'])

    def _fmt(self, amount):
        return formatLang(self.env, amount, currency_obj=self.env.company.currency_id)

    def _assert_message_has_figures(self, order, credit_limit, outstanding, current_amount):
        message = order.credit_limit_warning_message
        self.assertTrue(message)
        self.assertIn(self._fmt(credit_limit), message)
        self.assertIn(self._fmt(outstanding), message)
        self.assertIn(self._fmt(current_amount), message)

    def test_none_when_credit_limit_unset(self):
        """No credit_limit configured -> always 'none', regardless of order size."""
        self.assertFalse(self.customer.credit_limit)
        order = self._create_order(10000.0)
        self.assertEqual(order.credit_limit_warning_level, 'none')
        self.assertFalse(order.credit_limit_warning_message)

    def test_none_under_80_percent(self):
        """Projected exposure below 80% of the limit -> 'none'."""
        self.customer.credit_limit = 1000.0
        self._build_outstanding(credit_to_invoice=300.0)
        order = self._create_order(400.0)  # (300 + 400) / 1000 = 0.7
        self.assertEqual(order.credit_limit_warning_level, 'none')
        self.assertFalse(order.credit_limit_warning_message)

    def test_warning_at_exactly_80_percent(self):
        """Projected exposure at exactly 80% of the limit -> 'warning' (boundary)."""
        self.customer.credit_limit = 1000.0
        self._build_outstanding(credit=200.0, credit_to_invoice=200.0)
        order = self._create_order(400.0)  # (200 + 200 + 400) / 1000 = 0.8
        self.assertEqual(order.credit_limit_warning_level, 'warning')
        self._assert_message_has_figures(order, 1000.0, 400.0, 400.0)

    def test_warning_just_under_100_percent(self):
        """Projected exposure just below 100% of the limit -> 'warning'."""
        self.customer.credit_limit = 1000.0
        self._build_outstanding(credit_to_invoice=500.0)
        order = self._create_order(499.0)  # (500 + 499) / 1000 = 0.999
        self.assertEqual(order.credit_limit_warning_level, 'warning')
        self._assert_message_has_figures(order, 1000.0, 500.0, 499.0)

    def test_danger_at_and_above_100_percent(self):
        """Projected exposure at exactly 100% of the limit, and above it, -> 'danger' (boundary)."""
        self.customer.credit_limit = 1000.0
        self._build_outstanding(credit_to_invoice=500.0)

        order_at_limit = self._create_order(500.0)  # (500 + 500) / 1000 = 1.0
        self.assertEqual(order_at_limit.credit_limit_warning_level, 'danger')
        self._assert_message_has_figures(order_at_limit, 1000.0, 500.0, 500.0)

        order_over_limit = self._create_order(700.0)  # (500 + 700) / 1000 = 1.2
        self.assertEqual(order_over_limit.credit_limit_warning_level, 'danger')
        self._assert_message_has_figures(order_over_limit, 1000.0, 500.0, 700.0)

    def test_none_when_order_not_draft_or_sent(self):
        """A confirmed order must not show the warning, even if it would be over limit
        while still a quotation (matches stock's own state gating)."""
        self.customer.credit_limit = 1000.0
        self._build_outstanding(credit_to_invoice=500.0)
        order = self._create_order(700.0)  # (500 + 700) / 1000 = 1.2 -> would be 'danger'
        order.action_confirm()
        self.assertEqual(order.state, 'sale')
        self.assertEqual(order.credit_limit_warning_level, 'none')
        self.assertFalse(order.credit_limit_warning_message)

    def test_none_when_company_credit_limit_feature_disabled(self):
        """No warning at all when the company has turned off account_use_credit_limit,
        even for an over-limit draft order."""
        self.env.company.account_use_credit_limit = False
        self.customer.credit_limit = 1000.0
        self._build_outstanding(credit_to_invoice=500.0)
        order = self._create_order(700.0)  # (500 + 700) / 1000 = 1.2 -> would be 'danger'
        self.assertEqual(order.credit_limit_warning_level, 'none')
        self.assertFalse(order.credit_limit_warning_message)
