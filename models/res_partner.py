# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Configuration constants - modify these to change behavior
ORIGIN_LAT = 38.3353600
ORIGIN_LON = -82.7815527
EARTH_RADIUS_MILES = 3959
PI = 3.14159


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_partner_distance = fields.Float(
        string='Distance from Origin (miles)',
        digits=(10, 2),
        help='Calculated distance from origin point to customer location',
        readonly=True,
    )

    def calculate_distance_from_origin(self):
        """
        Calculate and store distance from fixed origin point to partner location.
        
        Workflow:
        1. Check if partner has GPS coordinates
        2. If missing, attempt automatic geocoding
        3. Calculate distance using approximation formula
        4. Store result in x_partner_distance field
        5. Return calculated distance
        
        Returns:
            float: Distance in miles
            
        Raises:
            UserError: If geocoding fails or coordinates cannot be obtained
        """
        self.ensure_one()
        
        # Check if coordinates exist
        if not self.partner_latitude or not self.partner_longitude:
            _logger.info(
                f"Partner {self.name} (ID: {self.id}) missing GPS coordinates. "
                "Attempting automatic geocoding..."
            )
            
            # Attempt automatic geocoding
            try:
                self.geo_localize()
                
                # Verify geocoding was successful
                if not self.partner_latitude or not self.partner_longitude:
                    error_msg = _(
                        "Unable to calculate delivery cost for %s.\n\n"
                        "The customer's address could not be geocoded. "
                        "Please verify that the address is complete and correct:\n"
                        "- Street address\n"
                        "- City\n"
                        "- State/Province\n"
                        "- ZIP/Postal code\n"
                        "- Country"
                    ) % self.name
                    _logger.error(
                        f"Geocoding failed for partner {self.name} (ID: {self.id}). "
                        f"Address: {self._display_address()}"
                    )
                    raise UserError(error_msg)
                    
                _logger.info(
                    f"Successfully geocoded partner {self.name} (ID: {self.id}). "
                    f"Coordinates: ({self.partner_latitude}, {self.partner_longitude})"
                )
                
            except Exception as e:
                error_msg = _(
                    "Failed to geocode address for %s.\n\n"
                    "Error: %s\n\n"
                    "Please ensure the customer has a valid, complete address."
                ) % (self.name, str(e))
                _logger.error(
                    f"Exception during geocoding for partner {self.name} (ID: {self.id}): {str(e)}"
                )
                raise UserError(error_msg)
        
        # Calculate distance
        distance = self._approximate_distance(
            ORIGIN_LAT,
            ORIGIN_LON,
            self.partner_latitude,
            self.partner_longitude
        )
        
        # Store calculated distance
        self.x_partner_distance = distance
        
        _logger.info(
            f"Calculated distance for partner {self.name} (ID: {self.id}): "
            f"{distance:.2f} miles from origin ({ORIGIN_LAT}, {ORIGIN_LON})"
        )
        
        return distance

    def _approximate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate approximate distance between two GPS coordinates using simplified formula.
        
        This is a rough approximation suitable for relatively short distances.
        For more accurate results over longer distances, consider implementing
        the Haversine formula.
        
        Args:
            lat1 (float): Origin latitude
            lon1 (float): Origin longitude
            lat2 (float): Destination latitude
            lon2 (float): Destination longitude
            
        Returns:
            float: Approximate distance in miles
        """
        # Convert latitude and longitude differences to radians
        lat_diff_rad = (lat2 - lat1) * PI / 180
        lon_diff_rad = (lon2 - lon1) * PI / 180
        
        # Calculate distance using simplified formula
        distance = EARTH_RADIUS_MILES * ((lat_diff_rad**2) + (lon_diff_rad**2))**0.5
        
        return distance

    def _display_address(self):
        """
        Helper method to display partner address for logging/error messages.
        
        Returns:
            str: Formatted address string
        """
        address_parts = [
            self.street or '',
            self.street2 or '',
            self.city or '',
            self.state_id.name if self.state_id else '',
            self.zip or '',
            self.country_id.name if self.country_id else '',
        ]
        return ', '.join(filter(None, address_parts))
