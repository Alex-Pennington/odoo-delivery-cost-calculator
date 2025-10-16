# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Configuration constants
DELIVERY_PRODUCT_NAME = 'Delivery'
DEFAULT_RATE_PER_MILE = 2.5  # Fallback if setting not configured


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_delivery_line = fields.Boolean(
        string='Is Delivery Line',
        compute='_compute_is_delivery_line',
        store=True,
        help='Indicates if this line is for delivery service'
    )
    
    delivery_cost_calculated = fields.Boolean(
        string='Delivery Cost Calculated',
        default=False,
        help='Flag to prevent automatic recalculation of delivery cost'
    )

    def _get_rate_per_mile(self):
        """
        Get the configured rate per mile from system settings.
        
        Returns:
            float: Rate per mile for delivery cost calculation
        """
        ICP = self.env['ir.config_parameter'].sudo()
        return float(ICP.get_param(
            'delivery_cost_calculator.rate_per_mile',
            DEFAULT_RATE_PER_MILE
        ))

    @api.depends('product_id', 'product_id.name', 'product_id.type', 'product_id.active')
    def _compute_is_delivery_line(self):
        """
        Determine if this order line is a delivery line.
        
        Criteria:
        - Product name equals DELIVERY_PRODUCT_NAME (case-insensitive)
        - Product type is 'service'
        - Product is active (not archived)
        """
        for line in self:
            line.is_delivery_line = (
                line.product_id and
                line.product_id.active and
                line.product_id.type == 'service' and
                line.product_id.name and
                line.product_id.name.strip().lower() == DELIVERY_PRODUCT_NAME.lower()
            )

    @api.onchange('product_id')
    def _onchange_product_delivery_cost(self):
        """
        Automatically calculate delivery cost when delivery product is selected.
        
        Triggered when user manually adds delivery product to order line.
        Handles validation, calculation, and user feedback.
        """
        # Check if this is a delivery line and hasn't been calculated yet
        if not self.is_delivery_line or self.delivery_cost_calculated:
            return

        # Validate that customer is selected
        if not self.order_id.partner_id:
            return {
                'warning': {
                    'title': _('Customer Required'),
                    'message': _(
                        'Please select a customer before adding delivery service. '
                        'The delivery cost is calculated based on the customer\'s location.'
                    )
                }
            }

        # Perform delivery cost calculation
        try:
            partner = self.order_id.partner_id
            
            # Get configured rate per mile
            rate_per_mile = self._get_rate_per_mile()
            
            # Calculate distance (includes auto-geocoding if needed)
            distance = partner.calculate_distance_from_origin()
            
            # Calculate delivery cost
            delivery_cost = distance * rate_per_mile
            
            # Update order line with calculated price
            self.price_unit = delivery_cost
            self.delivery_cost_calculated = True
            
            _logger.info(
                f"Delivery cost calculated for SO {self.order_id.name}: "
                f"Distance={distance:.2f} miles, Rate=${rate_per_mile:.2f}/mile, "
                f"Total=${delivery_cost:.2f}"
            )
            
            # Show confirmation message to user
            return {
                'warning': {
                    'title': _('Delivery Cost Calculated'),
                    'message': _(
                        'Delivery cost has been automatically calculated:\n\n'
                        'Customer: %s\n'
                        'Distance: %.2f miles\n'
                        'Rate: $%.2f per mile\n'
                        'Total Delivery Cost: $%.2f\n\n'
                        'This price is now locked and will not change automatically '
                        'if the customer address is updated.'
                    ) % (partner.name, distance, rate_per_mile, delivery_cost)
                }
            }
            
        except UserError as e:
            # Re-raise UserError for proper display to user
            _logger.warning(f"Delivery cost calculation failed: {str(e)}")
            raise
            
        except Exception as e:
            # Log unexpected errors and show user-friendly message
            _logger.error(
                f"Unexpected error calculating delivery cost for SO {self.order_id.name}: {str(e)}",
                exc_info=True
            )
            raise UserError(_(
                'An unexpected error occurred while calculating delivery cost:\n\n%s\n\n'
                'Please contact system administrator if this problem persists.'
            ) % str(e))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to handle delivery cost calculation for programmatically created lines.
        
        This ensures delivery cost is calculated for:
        - Website/eCommerce orders
        - API-created orders
        - Imported orders
        - Any other programmatic order creation
        """
        lines = super(SaleOrderLine, self).create(vals_list)
        
        # Process each newly created line
        for line in lines:
            # Only process delivery lines that haven't been calculated
            if line.is_delivery_line and not line.delivery_cost_calculated:
                
                # Validate customer exists
                if not line.order_id.partner_id:
                    _logger.warning(
                        f"Delivery line created without customer on SO {line.order_id.name}. "
                        "Skipping automatic cost calculation."
                    )
                    continue
                
                try:
                    partner = line.order_id.partner_id
                    
                    # Get configured rate per mile
                    rate_per_mile = line._get_rate_per_mile()
                    
                    # Calculate distance
                    distance = partner.calculate_distance_from_origin()
                    
                    # Calculate and set delivery cost
                    delivery_cost = distance * rate_per_mile
                    line.write({
                        'price_unit': delivery_cost,
                        'delivery_cost_calculated': True,
                    })
                    
                    _logger.info(
                        f"Delivery cost auto-calculated on create for SO {line.order_id.name}: "
                        f"Distance={distance:.2f} miles, Cost=${delivery_cost:.2f}"
                    )
                    
                except UserError as e:
                    # Log error but don't block order creation
                    _logger.error(
                        f"Could not calculate delivery cost for SO {line.order_id.name}: {str(e)}"
                    )
                    # Optionally, you could add a note to the order here
                    
                except Exception as e:
                    _logger.error(
                        f"Unexpected error calculating delivery cost on create for "
                        f"SO {line.order_id.name}: {str(e)}",
                        exc_info=True
                    )
        
        return lines


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_recalculate_delivery_cost(self):
        """
        Manually recalculate delivery cost for this order.
        
        This action:
        1. Finds delivery line(s) in the order
        2. Resets the calculation flag
        3. Triggers recalculation
        4. Updates the line with new cost
        
        Can be called from a button or action in the UI.
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_(
                'Cannot calculate delivery cost: No customer selected.\n\n'
                'Please select a customer first.'
            ))
        
        # Find all delivery lines
        delivery_lines = self.order_line.filtered('is_delivery_line')
        
        if not delivery_lines:
            raise UserError(_(
                'No delivery line found in this order.\n\n'
                'Please add the "Delivery" product to the order first.'
            ))
        
        # Process each delivery line
        for line in delivery_lines:
            try:
                # Get configured rate per mile
                rate_per_mile = line._get_rate_per_mile()
                
                # Recalculate distance
                distance = self.partner_id.calculate_distance_from_origin()
                
                # Calculate new delivery cost
                delivery_cost = distance * rate_per_mile
                
                # Update line
                line.write({
                    'price_unit': delivery_cost,
                    'delivery_cost_calculated': True,
                })
                
                _logger.info(
                    f"Manual recalculation for SO {self.name}: "
                    f"Distance={distance:.2f} miles, Cost=${delivery_cost:.2f}"
                )
                
            except Exception as e:
                _logger.error(
                    f"Error during manual recalculation for SO {self.name}: {str(e)}",
                    exc_info=True
                )
                raise
        
        # Show success message
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _(
                    'Delivery cost recalculated successfully:\n'
                    'Distance: %.2f miles\n'
                    'Rate: $%.2f per mile\n'
                    'Total: $%.2f'
                ) % (distance, rate_per_mile, delivery_cost),
                'type': 'success',
                'sticky': False,
            }
        }

    def _get_delivery_cost_info(self):
        """
        Helper method to get delivery cost information for this order.
        
        Returns:
            dict: Dictionary with delivery cost details or None if no delivery line
        """
        self.ensure_one()
        
        delivery_line = self.order_line.filtered('is_delivery_line')[:1]
        
        if not delivery_line:
            return None
        
        # Get configured rate per mile
        rate_per_mile = delivery_line._get_rate_per_mile()
        
        # Calculate current distance (don't rely on stored field)
        try:
            distance = self.partner_id.calculate_distance_from_origin()
        except:
            distance = 0.0
        
        return {
            'line': delivery_line,
            'distance': distance,
            'rate': rate_per_mile,
            'cost': delivery_line.price_unit,
            'calculated': delivery_line.delivery_cost_calculated,
        }
