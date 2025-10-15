# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Configuration constants - modify these to change behavior
ORIGIN_LAT = 38.3353600
ORIGIN_LON = -82.7815527
RATE_PER_MILE = 3.0
MAX_DISTANCE_MILES = 60.0
MAX_ORDER_QUANTITY = 8


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(
        selection_add=[('gps', 'GPS Distance Based')],
        ondelete={'gps': 'set default'}
    )

    def gps_rate_shipment(self, order):
        """
        Calculate shipping rate based on GPS distance from fixed origin.
        
        This method is called by Odoo's delivery module during checkout to:
        1. Determine if this shipping method is available
        2. Calculate the shipping cost if available
        
        Availability Rules:
        - Customer must be within MAX_DISTANCE_MILES (60 miles)
        - Order total quantity must be less than MAX_ORDER_QUANTITY (8 units)
        - Customer must have valid geocodable address
        
        If any rule fails, returns success=False (method won't appear in checkout)
        
        Args:
            order (sale.order): The sales order to calculate shipping for
            
        Returns:
            dict: {
                'success': bool,
                'price': float,
                'error_message': str or False,
                'warning_message': str or False
            }
        """
        # Get shipping partner (delivery address, fallback to invoice address)
        partner = order.partner_shipping_id or order.partner_id
        
        if not partner:
            _logger.warning(
                f"GPS delivery: No partner found for order {order.name}"
            )
            return {
                'success': False,
                'price': 0.0,
                'error_message': False,
                'warning_message': False
            }
        
        # Calculate total order quantity (excluding delivery/service products)
        total_qty = sum(
            line.product_uom_qty 
            for line in order.order_line 
            if line.product_id.type in ['product', 'consu']  # Only physical products
        )
        
        _logger.debug(
            f"GPS delivery check for order {order.name}: "
            f"Total quantity = {total_qty} units"
        )
        
        # Check quantity constraint
        if total_qty >= MAX_ORDER_QUANTITY:
            _logger.info(
                f"GPS delivery unavailable for order {order.name}: "
                f"Quantity {total_qty} >= {MAX_ORDER_QUANTITY} units"
            )
            return {
                'success': False,
                'price': 0.0,
                'error_message': False,
                'warning_message': False
            }
        
        # Check if partner has GPS coordinates
        if not partner.partner_latitude or not partner.partner_longitude:
            _logger.info(
                f"GPS delivery: Partner {partner.name} (ID: {partner.id}) "
                "missing coordinates. Attempting geocoding..."
            )
            
            try:
                # Attempt automatic geocoding
                partner.geo_localize()
                
                # Verify geocoding succeeded
                if not partner.partner_latitude or not partner.partner_longitude:
                    _logger.warning(
                        f"GPS delivery unavailable: Geocoding failed for "
                        f"partner {partner.name} (ID: {partner.id})"
                    )
                    return {
                        'success': False,
                        'price': 0.0,
                        'error_message': False,
                        'warning_message': False
                    }
                
                _logger.info(
                    f"GPS delivery: Successfully geocoded partner {partner.name} "
                    f"({partner.partner_latitude}, {partner.partner_longitude})"
                )
                
            except Exception as e:
                _logger.warning(
                    f"GPS delivery unavailable: Geocoding exception for "
                    f"partner {partner.name} (ID: {partner.id}): {str(e)}"
                )
                return {
                    'success': False,
                    'price': 0.0,
                    'error_message': False,
                    'warning_message': False
                }
        
        # Calculate distance using existing method from res.partner
        try:
            distance = partner.calculate_distance_from_origin()
            
            _logger.debug(
                f"GPS delivery: Calculated distance for {partner.name}: "
                f"{distance:.2f} miles"
            )
            
        except Exception as e:
            _logger.error(
                f"GPS delivery unavailable: Distance calculation failed for "
                f"order {order.name}: {str(e)}",
                exc_info=True
            )
            return {
                'success': False,
                'price': 0.0,
                'error_message': False,
                'warning_message': False
            }
        
        # Check distance constraint
        if distance > MAX_DISTANCE_MILES:
            _logger.info(
                f"GPS delivery unavailable for order {order.name}: "
                f"Distance {distance:.2f} miles > {MAX_DISTANCE_MILES} miles"
            )
            return {
                'success': False,
                'price': 0.0,
                'error_message': False,
                'warning_message': False
            }
        
        # Calculate shipping price
        price = distance * RATE_PER_MILE
        
        _logger.info(
            f"GPS delivery available for order {order.name}: "
            f"Distance={distance:.2f} miles, Price=${price:.2f}"
        )
        
        return {
            'success': True,
            'price': price,
            'error_message': False,
            'warning_message': False
        }

    def gps_send_shipping(self, pickings):
        """
        Process shipment for GPS delivery method.
        
        Since this is a custom local delivery (not using external shipping API),
        we simply mark the shipment as processed and return tracking info.
        
        Args:
            pickings (stock.picking): Delivery order(s) to process
            
        Returns:
            list: List of dicts with tracking information for each picking
        """
        res = []
        
        for picking in pickings:
            # Generate a simple tracking reference
            tracking_ref = f"LOCAL-{picking.name}"
            
            _logger.info(
                f"GPS delivery: Processing shipment {picking.name} "
                f"with tracking {tracking_ref}"
            )
            
            res.append({
                'exact_price': picking.carrier_id.gps_rate_shipment(picking.sale_id)['price'] if picking.sale_id else 0.0,
                'tracking_number': tracking_ref
            })
        
        return res

    def gps_get_tracking_link(self, picking):
        """
        Generate tracking link for GPS delivery.
        
        Since this is local delivery, return a simple status page or False.
        
        Args:
            picking (stock.picking): Delivery order
            
        Returns:
            str or bool: Tracking URL or False
        """
        # For local delivery, you might return a link to internal delivery status
        # or just return False if no tracking URL is available
        return False

    def gps_cancel_shipment(self, picking):
        """
        Cancel shipment for GPS delivery.
        
        Since no external API is involved, just log the cancellation.
        
        Args:
            picking (stock.picking): Delivery order to cancel
        """
        _logger.info(
            f"GPS delivery: Cancelled shipment {picking.name}"
        )
        
        # Remove tracking number if needed
        picking.write({
            'carrier_tracking_ref': False,
        })
