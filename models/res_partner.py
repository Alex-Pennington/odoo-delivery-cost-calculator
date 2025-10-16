# -*- coding: utf-8 -*-

import logging
import math
import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Default configuration constants - can be overridden in Settings
DEFAULT_ORIGIN_LAT = 38.48358903556404
DEFAULT_ORIGIN_LON = -82.7803864690895
DEFAULT_RATE_PER_MILE = 2.5
DEFAULT_MAX_DELIVERY_DISTANCE = 75.0
DEFAULT_ROAD_MULTIPLIER = 1.3  # Fallback: roads typically 30% longer than straight line
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
            dict: Dictionary with keys: origin_lat, origin_lon, rate_per_mile, max_distance,
                  road_multiplier, google_api_key, use_google_maps
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
            'road_multiplier': float(ICP.get_param(
                'delivery_cost_calculator.road_multiplier',
                DEFAULT_ROAD_MULTIPLIER
            )),
            'google_api_key': ICP.get_param(
                'delivery_cost_calculator.google_api_key',
                ''
            ),
            'use_google_maps': ICP.get_param(
                'delivery_cost_calculator.use_google_maps',
                'False'
            ) == 'True',
        }

    def _get_google_maps_distance(self, origin_lat, origin_lon, dest_lat, dest_lon):
        """
        Get actual driving distance using Google Maps Distance Matrix API.
        
        This provides real-world road distances considering:
        - Actual road networks
        - One-way streets
        - Turn restrictions
        - Typical routing
        
        Requires:
        - Google Cloud Platform account
        - Distance Matrix API enabled
        - API key configured in settings
        
        Cost: Approximately $0.005 per calculation
        Documentation: https://developers.google.com/maps/documentation/distance-matrix
        
        Args:
            origin_lat (float): Origin latitude in decimal degrees
            origin_lon (float): Origin longitude in decimal degrees
            dest_lat (float): Destination latitude in decimal degrees
            dest_lon (float): Destination longitude in decimal degrees
            
        Returns:
            float: Driving distance in miles
            
        Raises:
            Exception: If API call fails (will be caught and fallback to Haversine)
        """
        settings = self._get_delivery_settings()
        api_key = settings.get('google_api_key', '')
        
        if not api_key:
            _logger.warning(
                "Google Maps API key not configured. "
                "Falling back to Haversine × road multiplier."
            )
            straight = self._haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
            return straight * settings.get('road_multiplier', DEFAULT_ROAD_MULTIPLIER)
        
        url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            'origins': f"{origin_lat},{origin_lon}",
            'destinations': f"{dest_lat},{dest_lon}",
            'units': 'imperial',  # Get results in miles
            'mode': 'driving',
            'key': api_key
        }
        
        try:
            _logger.info(
                f"Calling Google Maps API for distance: "
                f"({origin_lat},{origin_lon}) → ({dest_lat},{dest_lon})"
            )
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK':
                element = data['rows'][0]['elements'][0]
                
                if element['status'] == 'OK':
                    # Distance is in meters, convert to miles
                    distance_meters = element['distance']['value']
                    distance_miles = distance_meters * 0.000621371
                    
                    _logger.info(
                        f"Google Maps API returned: {distance_miles:.2f} miles "
                        f"(duration: {element['duration']['text']})"
                    )
                    
                    return distance_miles
                else:
                    _logger.warning(
                        f"Google Maps API element status: {element['status']}. "
                        "Falling back to Haversine × road multiplier."
                    )
                    straight = self._haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
                    return straight * settings.get('road_multiplier', DEFAULT_ROAD_MULTIPLIER)
            else:
                _logger.warning(
                    f"Google Maps API error: {data.get('status')} - "
                    f"{data.get('error_message', 'No error message')}. "
                    "Falling back to Haversine × road multiplier."
                )
                straight = self._haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
                return straight * settings.get('road_multiplier', DEFAULT_ROAD_MULTIPLIER)
                
        except requests.RequestException as e:
            _logger.error(
                f"Google Maps API request failed: {str(e)}. "
                "Falling back to Haversine × road multiplier."
            )
            straight = self._haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
            return straight * settings.get('road_multiplier', DEFAULT_ROAD_MULTIPLIER)
        except Exception as e:
            _logger.error(
                f"Unexpected error calling Google Maps API: {str(e)}. "
                "Falling back to Haversine × road multiplier.",
                exc_info=True
            )
            straight = self._haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)
            return straight * settings.get('road_multiplier', DEFAULT_ROAD_MULTIPLIER)

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
        
        # Track which calculation method was used
        calculation_method = None
        
        # Calculate distance using Google Maps API or Haversine formula
        try:
            if settings.get('use_google_maps', False):
                # Use Google Maps Distance Matrix API for accurate road distance
                distance = self._get_google_maps_distance(
                    settings['origin_lat'],
                    settings['origin_lon'],
                    self.partner_latitude,
                    self.partner_longitude
                )
                calculation_method = 'google_maps'
                _logger.info(
                    f"Using Google Maps API - calculated distance: {distance:.2f} miles"
                )
            else:
                # Use Haversine formula with road multiplier
                straight_line = self._haversine_distance(
                    settings['origin_lat'],
                    settings['origin_lon'],
                    self.partner_latitude,
                    self.partner_longitude
                )
                road_multiplier = settings.get('road_multiplier', DEFAULT_ROAD_MULTIPLIER)
                distance = straight_line * road_multiplier
                calculation_method = 'haversine'
                
                _logger.info(
                    f"Using Haversine × {road_multiplier}: "
                    f"straight-line {straight_line:.2f} mi → road estimate {distance:.2f} mi"
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
            f"{distance:.2f} miles from origin ({settings['origin_lat']}, {settings['origin_lon']}) "
            f"using {calculation_method}"
        )
        
        # Return both distance and calculation method
        # For backwards compatibility, can be called as just: distance = partner.calculate_distance_from_origin()
        # Or with unpacking: distance, method = partner.calculate_distance_from_origin()
        return distance, calculation_method

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
            >>> distance = self._haversine_distance(38.48358903556404, -82.7803864690895, 
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
