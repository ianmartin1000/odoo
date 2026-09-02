# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale Credit Limit Warning',
    'version': '1.0',
    'category': 'Sales/Sales',
    'summary': 'Warn salespeople when an order pushes a customer over their credit limit',
    'description': """
Adds a non-stored warning level and message to Sale Orders based on the
customer's outstanding credit exposure (posted + to-invoice + this order)
relative to their credit limit.
    """,
    'depends': ['sale'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}
