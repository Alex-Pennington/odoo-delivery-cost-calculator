# -*- coding: utf-8 -*-

import logging
import math
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Default configuration constants - can be overridden in Settings
DEFAULT_ORIGIN_LAT = 38.3353600
DEFAULT_ORIGIN_LON = -82.7815527
DEFAULT_RATE_PER_MILE = 3.0
DEFAULT_MAX_DELIVERY_DISTANCE = 100.0
EARTH_RADIUS_MILES = 3959


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Legacy field for backward compatibility
    # Some views/modules may reference this field
    # Our module calculates distance dynamically and doesn't populate this field
    x_partner_distance = fields.Float(
        string='Distance from Origin (miles)',
        digits=(10, 2),
        help='Legacy field - distance is now calculated dynamically when needed',
        readonly=True,
        default=0.0,
    )

    def _get_delivery_settings(self):
        """
        Get delivery configuration settings from system parameters.
        Falls back to defaults if settings not configured.
        
        Returns:
            dict: Dictionary with keys: origin_lat, origin_lon, rate_per_mile, max_distance
        """
        ICP = self.env['ir.config_parameter'].sudo()
        
        return {
            'origin_lat': float(ICP.get_param(
                'delivery_cost_calculator.origin_latitude',
                DEFAULT_ORIGIN_LAT
            )),
            'origin_lon': float(ICP.get_param(
                'delivery_cost_calculator.origin_longitude',
                DEFAULT_ORIGIN_LON
            )),
            'rate_per_mile': float(ICP.get_param(
                'delivery_cost_calculator.rate_per_mile',
                DEFAULT_RATE_PER_MILE
            )),
            'max_distance': float(ICP.get_param(
                'delivery_cost_calculator.max_distance',
                DEFAULT_MAX_DELIVERY_DISTANCE
            )),
        }

    def calculate_distance_from_origin(self):
        """
        Calculate distance from fixed origin point to partner location.
        Validates coordinates and stores accurate distance in x_partner_distance field.
        
        Workflow:
        1. Check if partner has GPS coordinates
        2. If missing, attempt automatic geocoding
        3. Validate coordinates are reasonable
        4. Calculate distance using Haversine formula
        5. Store and return calculated distance
        
        Returns:
            float: Distance in miles
            
        Raises:
            UserError: If geocoding fails or coordinates are invalid
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
        
        # Validate coordinates are reasonable
        validation_error = self._validate_coordinates()
        if validation_error:
            _logger.error(
                f"Invalid coordinates for partner {self.name} (ID: {self.id}): "
                f"Lat: {self.partner_latitude}, Lon: {self.partner_longitude}. "
                f"Error: {validation_error}"
            )
            raise UserError(_(
                "Invalid GPS coordinates for %s.\n\n"
                "%s\n\n"
                "Coordinates: Latitude %s, Longitude %s\n\n"
                "Please verify the customer's address and try geocoding again."
            ) % (self.name, validation_error, self.partner_latitude, self.partner_longitude))
        
        # Get delivery settings
        settings = self._get_delivery_settings()
        
        # Calculate distance using Haversine formula
        try:
            distance = self._haversine_distance(
                settings['origin_lat'],
                settings['origin_lon'],
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
        
        # Validate customer is within delivery range
        if distance > settings['max_distance']:
            _logger.warning(
                f"Partner {self.name} (ID: {self.id}) is outside delivery range: "
                f"{distance:.2f} miles (max: {settings['max_distance']} miles)"
            )
            raise UserError(_(
                "Delivery Not Available for %s\n\n"
                "Customer location is %.2f miles from origin.\n"
                "Maximum delivery distance: %.0f miles.\n\n"
                "This customer is outside the delivery service area."
            ) % (self.name, distance, settings['max_distance']))
        
        _logger.info(
            f"Calculated distance for partner {self.name} (ID: {self.id}): "
            f"{distance:.2f} miles from origin ({settings['origin_lat']}, {settings['origin_lon']})"
        )
        
        return distance

    def _validate_coordinates(self):
        """
        Validate that partner coordinates are reasonable and usable.
        
        Checks for:
        - Zero or null values
        - Out of valid range (lat: -90 to 90, lon: -180 to 180)
        - Suspiciously large values (>1000) that indicate bad data
        
        Note: Distance validation (100-mile radius) is performed separately
        after coordinates are validated.
        
        Returns:
            str: Error message if validation fails, None if coordinates are valid
        """
        self.ensure_one()
        
        lat = self.partner_latitude
        lon = self.partner_longitude
        
        # Check for zero or null coordinates
        if not lat or not lon or (lat == 0.0 and lon == 0.0):
            return "Coordinates are zero or empty (geocoding may have failed)"
        
        # Check for obviously invalid values (>1000 suggests corrupt data)
        if abs(lat) > 1000 or abs(lon) > 1000:
            return f"Coordinates are impossibly large (Lat: {lat}, Lon: {lon})"
        
        # Check if coordinates are within valid range
        if not (-90 <= lat <= 90):
            return f"Latitude {lat} is out of valid range (-90 to 90)"
        
        if not (-180 <= lon <= 180):
            return f"Longitude {lon} is out of valid range (-180 to 180)"
        
        # Optional: Check if coordinates are in a reasonable area for delivery
        # For USA delivery, we might want to validate coordinates are roughly in North America
        # Uncomment these lines if you want stricter geographic validation:
        #
        # if not (15 <= lat <= 72):  # Roughly USA/Canada latitude range
        #     return f"Location appears to be outside delivery area (Latitude: {lat})"
        #
        # if not (-170 <= lon <= -50):  # Roughly USA/Canada longitude range  
        #     return f"Location appears to be outside delivery area (Longitude: {lon})"
        
        # Coordinates passed all validation checks
        return None

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
