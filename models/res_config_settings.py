# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Delivery Origin Configuration
    delivery_origin_latitude = fields.Float(
        string='Origin Latitude',
        config_parameter='delivery_cost_calculator.origin_latitude',
        default=38.48358903556404,
        digits=(12, 8),  # Total 12 digits, 8 after decimal point
        help='Latitude coordinate of delivery origin point (decimal degrees)',
    )
    
    delivery_origin_longitude = fields.Float(
        string='Origin Longitude',
        config_parameter='delivery_cost_calculator.origin_longitude',
        default=-82.7803864690895,
        digits=(12, 8),  # Total 12 digits, 8 after decimal point
        help='Longitude coordinate of delivery origin point (decimal degrees)',
    )
    
    # Pricing Configuration
    delivery_rate_per_mile = fields.Float(
        string='Rate per Mile',
        config_parameter='delivery_cost_calculator.rate_per_mile',
        default=2.5,
        digits=(10, 2),  # Like $2.50 or $12.99
        help='Cost per mile for delivery calculation (e.g., 2.5 = $2.50/mile)',
    )
    
    # Distance Restrictions
    delivery_max_distance = fields.Float(
        string='Maximum Delivery Distance',
        config_parameter='delivery_cost_calculator.max_distance',
        default=75.0,
        digits=(10, 2),  # Like 75.50 miles
        help='Maximum distance in miles for delivery service (customers beyond this distance will be rejected)',
    )
    
    # Order Quantity Restrictions
    delivery_max_order_quantity = fields.Integer(
        string='Maximum Order Quantity',
        config_parameter='delivery_cost_calculator.max_order_quantity',
        default=8,
        help='Maximum number of items allowed for GPS delivery carrier on website checkout',
    )
    
    # GPS Carrier Distance Limit (for website)
    delivery_gps_carrier_max_distance = fields.Float(
        string='GPS Carrier Max Distance',
        config_parameter='delivery_cost_calculator.gps_carrier_max_distance',
        default=60.0,
        digits=(10, 2),  # Like 60.50 miles
        help='Maximum distance in miles for GPS delivery carrier availability on website (separate from manual delivery limit)',
    )
    
    # Road Distance Adjustment
    delivery_road_multiplier = fields.Float(
        string='Road Distance Multiplier',
        config_parameter='delivery_cost_calculator.road_multiplier',
        default=1.3,
        digits=(10, 2),  # Like 1.25 or 1.40
        help='Multiply straight-line distance by this factor to estimate road distance. '
             'Typical values: 1.2 (straight roads), 1.3 (average), 1.4 (winding roads). '
             'Only used when Google Maps API is disabled.',
    )
    
    # Google Maps API Configuration
    delivery_google_api_key = fields.Char(
        string='Google Maps API Key',
        config_parameter='delivery_cost_calculator.google_api_key',
        help='Google Cloud Platform API key for Distance Matrix API. '
             'Get one at: https://console.cloud.google.com/ '
             'Costs approximately $0.005 per distance calculation.',
    )
    
    delivery_use_google_maps = fields.Boolean(
        string='Use Google Maps for Distance',
        config_parameter='delivery_cost_calculator.use_google_maps',
        default=False,
        help='Enable to use Google Maps Distance Matrix API for accurate road distances. '
             'Requires API key. When disabled, uses Haversine formula × road multiplier.',
    )
