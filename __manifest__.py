# -*- coding: utf-8 -*-
{
    'name': 'Delivery Cost Calculator',
    'version': '17.0.4.0.0',
    'category': 'Sales',
    'summary': 'Automatic delivery cost calculation with Google Maps routing support',
    'description': """
        Delivery Cost Calculator
        ========================
        
        Automatically calculates delivery costs when a "Delivery" product is added to sales orders.
        
        Features:
        ---------
        * Automatic GPS geocoding for customers without coordinates
        * Accurate distance calculation using Haversine formula
        * Configurable rate per mile ($2.50 default)
        * Price locking to prevent recalculation on address changes
        * Manual recalculation option
        * Works with both manual quotes and website orders
        * Custom GPS delivery carrier for website checkout
        * Smart availability rules (max 60 miles, max 8 units)
        * Comprehensive error handling and user feedback
        
        Website Checkout:
        -----------------
        * GPS Distance-Based Delivery appears as shipping option if:
          - Customer within 60 miles of origin
          - Order quantity less than 8 units
          - Valid geocodable address
        * Automatically calculates exact shipping cost
        * Silently hides if conditions not met
        * Requires website_sale_delivery module for e-commerce integration
        
        Configuration:
        --------------
        * Origin coordinates: (38.48358903556404, -82.7803864690895)
        * Rate: $2.50 per mile
        * Max distance (manual orders): 75 miles
        * Max distance (website): 60 miles
        * Max quantity: 8 units
        * Distance formula: Haversine (accurate great-circle distance)
        * Distance stored in res.partner.x_partner_distance field
        
        To customize, edit constants in models/res_partner.py and models/delivery_carrier.py
        
        Note: v17.0.3.0 replaces inaccurate flat-Earth approximation with Haversine formula.
        Existing distances may need recalculation for accuracy.
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'sale',
        'base_geolocalize',
        'delivery',
    ],
    'data': [
        'data/delivery_carrier_data.xml',
        'views/sale_order_views.xml',
        'views/res_config_settings_views.xml',
        'views/delivery_carrier_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
