# -*- coding: utf-8 -*-
{
    'name': 'Delivery Cost Calculator',
    'version': '17.0.1.0.0',
    'category': 'Sales',
    'summary': 'Automatic delivery cost calculation based on GPS distance',
    'description': """
        Delivery Cost Calculator
        ========================
        
        Automatically calculates delivery costs when a "Delivery" product is added to sales orders.
        
        Features:
        ---------
        * Automatic GPS geocoding for customers without coordinates
        * Distance calculation from fixed origin point
        * Configurable rate per mile ($3.00 default)
        * Price locking to prevent recalculation on address changes
        * Manual recalculation option
        * Works with both manual quotes and website orders
        * Comprehensive error handling and user feedback
        
        Configuration:
        --------------
        * Origin coordinates: (38.3353600, -82.7815527)
        * Rate: $3.00 per mile
        * Distance stored in res.partner.x_partner_distance field
        
        To customize, edit constants in models/sale_order.py
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'base_geolocalize',
    ],
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
