# -*- coding: utf-8 -*-

import logging
import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Configuration constants - modify these to change behavior
ORIGIN_LAT = 38.3353600
ORIGIN_LON = -82.7815527
EARTH_RADIUS_MILES = 3959


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
                        f"Address: {self._format_address_for_log()}"
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
        
        # Calculate distance using Haversine formula
        try:
            distance = self._haversine_distance(
                ORIGIN_LAT,
                ORIGIN_LON,
                self.partner_latitude,
                self.partner_longitude
            )
        except Exception as e:
            _logger.error(
                f"Distance calculation failed for partner {self.name} (ID: {self.id}): {str(e)}"
            )
            raise UserError(_(
                "Failed to calculate distance for %s.\n\n"
                "Error: %s"
            ) % (self.name, str(e)))
        
        # Store calculated distance
        self.x_partner_distance = distance
        
        _logger.info(
            f"Calculated distance for partner {self.name} (ID: {self.id}): "
            f"{distance:.2f} miles from origin ({ORIGIN_LAT}, {ORIGIN_LON})"
        )
        
        return distance

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate accurate great-circle distance between two GPS coordinates
        using the Haversine formula.
        
        The Haversine formula determines the shortest distance over the Earth's
        surface, giving an "as-the-crow-flies" distance between the points
        (ignoring hills, roads, etc.). This is significantly more accurate than
        flat-Earth approximations, especially over longer distances.
        
        Formula:
            a = sin²(Δlat/2) + cos(lat1) · cos(lat2) · sin²(Δlon/2)
            c = 2 · asin(√a)
            d = R · c
        
        Where:
            - Δlat is the difference in latitude
            - Δlon is the difference in longitude
            - R is Earth's radius (3959 miles)
        
        Args:
            lat1 (float): Origin latitude in decimal degrees
            lon1 (float): Origin longitude in decimal degrees
            lat2 (float): Destination latitude in decimal degrees
            lon2 (float): Destination longitude in decimal degrees
            
        Returns:
            float: Great-circle distance in miles
            
        Example:
            >>> distance = self._haversine_distance(38.3353600, -82.7815527, 
            ...                                      38.5116816, -82.7264454)
            >>> print(f"{distance:.2f} miles")
            12.26 miles
        """
        # Earth's radius in miles
        R = EARTH_RADIUS_MILES
        
        # Convert latitude and longitude from degrees to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        # a = sin²(Δlat/2) + cos(lat1) · cos(lat2) · sin²(Δlon/2)
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        
        # c = 2 · asin(√a)
        c = 2 * math.asin(math.sqrt(a))
        
        # d = R · c
        distance = R * c
        
        return distance

    def _format_address_for_log(self):
        """
        Helper method to format partner address for logging/error messages.
        
        Note: Named differently from Odoo's _display_address() to avoid conflicts.
        
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
