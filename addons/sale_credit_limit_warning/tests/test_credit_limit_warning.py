# Part of Odoo. See LICENSE file for full copyright and licensing details.

from lxml import etree

from odoo.fields import Command
from odoo.tests import tagged, users
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

        # A salesperson with no Accounting access, mirroring the
        # 'notaccountman' fixture in addons/sale/tests/test_credit_limit.py, to
        # verify the new compute fields stay readable without AccessError.
        cls.sales_only_user = cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Sales Only User',
            'login': 'credit_warning_salesman',
            'email': 'credit_warning_salesman@example.com',
            'groups_id': [Command.set(cls.env.ref('sales_team.group_sale_salesman').ids)],
        })

        # Over-limit order for the access test below, created as superuser
        # since the restricted salesperson cannot write partner.credit_limit
        # (Contact management right) — only the read side is under test there.
        # A dedicated customer keeps this fixture isolated from cls.customer,
        # which other tests rely on having no credit_limit set by default.
        cls.over_limit_customer = cls.env['res.partner'].create({
            'name': 'Over Limit Customer',
            'credit_limit': 1000.0,
        })
        cls.over_limit_order = cls.env['sale.order'].create({
            'partner_id': cls.over_limit_customer.id,
            'order_line': [Command.create({
                'product_id': cls.product.id,
                'product_uom_qty': 1,
                'price_unit': 900.0,  # 900 / 1000 = 0.9 -> 'warning'
                'tax_id': False,
            })],
        })

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

    @users('credit_warning_salesman')
    def test_credit_limit_warning_access_without_accounting_group(self):
        """AC-ERROR-1 regression: a salesperson with only
        sales_team.group_sale_salesman (no Accounting access) must be able to
        read credit_limit_warning_level/_message on an over-limit order
        without hitting an AccessError — mirrors
        addons/sale/tests/test_credit_limit.py::test_credit_limit_access."""
        for group in self.env['res.partner']._fields['credit'].groups.split(','):
            self.assertFalse(self.env.user.has_group(group))

        order = self.over_limit_order.with_env(self.env)
        self.assertEqual(order.credit_limit_warning_level, 'warning')
        self.assertTrue(order.credit_limit_warning_message)

    def test_view_arch_hides_stock_banner_and_adds_two_tier_warning(self):
        """The inherited view must hide the stock partner_credit_warning banner
        and add the warning/danger pair driven by credit_limit_warning_level,
        following the two-tier alert-warning/alert-danger idiom in
        addons/account_edi/views/account_move_views.xml."""
        arch = self.env['sale.order'].get_view(view_id=self.env.ref('sale.view_order_form').id)['arch']
        tree = etree.fromstring(arch)

        stock_banners = tree.xpath("//div[hasclass('alert-warning')][field[@name='partner_credit_warning']]")
        self.assertEqual(len(stock_banners), 1, "The stock credit-warning banner should still be present in the arch")
        self.assertEqual(
            stock_banners[0].get('invisible'), '1', "The stock banner must be forced invisible on this view",
        )

        warning_message_divs = tree.xpath("//div[field[@name='credit_limit_warning_message']]")
        self.assertEqual(len(warning_message_divs), 2, "Both the warning and danger banners must be present")

        warning_div = next(d for d in warning_message_divs if 'alert-warning' in d.get('class', ''))
        danger_div = next(d for d in warning_message_divs if 'alert-danger' in d.get('class', ''))
        self.assertEqual(warning_div.get('invisible'), "credit_limit_warning_level != 'warning'")
        self.assertEqual(danger_div.get('invisible'), "credit_limit_warning_level != 'danger'")

    def test_warning_level_flips_as_order_lines_change(self):
        """End-to-end reactivity: editing order lines on a real quotation (not
        direct field assignment) must flip credit_limit_warning_level from
        'none' to 'warning' as amount_total crosses the 80% boundary."""
        self.customer.credit_limit = 1000.0
        order = self._create_order(700.0)  # 700 / 1000 = 0.7 -> 'none'
        self.assertEqual(order.credit_limit_warning_level, 'none')

        order.order_line.price_unit = 850.0  # 850 / 1000 = 0.85 -> 'warning'
        self.assertEqual(order.credit_limit_warning_level, 'warning')
