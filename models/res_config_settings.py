# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Delivery Origin Configuration
    delivery_origin_latitude = fields.Float(
        string='Origin Latitude',
        config_parameter='delivery_cost_calculator.origin_latitude',
        default=38.3353600,
        help='Latitude coordinate of delivery origin point (decimal degrees)',
    )
    
    delivery_origin_longitude = fields.Float(
        string='Origin Longitude',
        config_parameter='delivery_cost_calculator.origin_longitude',
        default=-82.7815527,
        help='Longitude coordinate of delivery origin point (decimal degrees)',
    )
    
    # Pricing Configuration
    delivery_rate_per_mile = fields.Float(
        string='Rate per Mile',
        config_parameter='delivery_cost_calculator.rate_per_mile',
        default=3.0,
        help='Cost per mile for delivery calculation (e.g., 3.0 = $3.00/mile)',
    )
    
    # Distance Restrictions
    delivery_max_distance = fields.Float(
        string='Maximum Delivery Distance',
        config_parameter='delivery_cost_calculator.max_distance',
        default=100.0,
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
        help='Maximum distance in miles for GPS delivery carrier availability on website (separate from manual delivery limit)',
    )
