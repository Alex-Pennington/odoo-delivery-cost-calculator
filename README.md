# Delivery Cost Calculator Module

## Overview
Automatic delivery cost calculation for Odoo 17 based on GPS distance from a fixed origin point.

## Features
- ✅ Automatic GPS geocoding for customers without coordinates
- ✅ Distance calculation from fixed origin point (38.3353600, -82.7815527)
- ✅ Configurable rate per mile ($3.00 default)
- ✅ Price locking - calculated cost doesn't change on address updates
- ✅ Manual recalculation option via button
- ✅ Works with manual quotes and website/e-commerce orders
- ✅ Comprehensive error handling and user feedback
- ✅ Detailed logging for debugging

## Installation

1. Copy the `delivery_cost_calculator` folder to your Odoo addons directory
2. Restart Odoo server
3. Update Apps List (Apps → Update Apps List)
4. Search for "Delivery Cost Calculator"
5. Click Install

## Configuration

### Prerequisites
Before installing this module, ensure you have:
1. A product named "Delivery" (type: service, active: true)
2. The `base_geolocalize` module installed
3. Customer field `x_partner_distance` created on res.partner (Float type)

### Customization
To modify default settings, edit the constants at the top of the model files:

**In `models/res_partner.py`:**
```python
ORIGIN_LAT = 38.3353600  # Origin latitude
ORIGIN_LON = -82.7815527  # Origin longitude
EARTH_RADIUS_MILES = 3959
PI = 3.14159
```

**In `models/sale_order.py`:**
```python
RATE_PER_MILE = 3.0  # Delivery rate per mile
DELIVERY_PRODUCT_NAME = 'Delivery'  # Name of delivery product
```

## Usage

### Automatic Calculation
1. Create a new Sales Order / Quotation
2. Select a customer
3. Add the "Delivery" product as a line item
4. The module automatically:
   - Checks if customer has GPS coordinates
   - Geocodes the address if coordinates are missing
   - Calculates distance from origin
   - Sets line price = distance × $3.00
   - Displays a popup with calculation details

### Manual Recalculation
If you need to recalculate delivery cost (e.g., customer moved):
1. Open the Sales Order
2. Click "Recalculate Delivery Cost" button (visible in Draft/Sent states)
3. New cost is calculated and applied

### Website/E-commerce Orders
The module automatically handles orders created through:
- Odoo eCommerce/website
- API integrations
- Order imports
- Any programmatic order creation

## How It Works

### Workflow
1. **Product Detection**: Identifies "Delivery" product (service type, active)
2. **Customer Validation**: Ensures customer is selected
3. **GPS Check**: Verifies customer has coordinates
4. **Auto-Geocoding**: If missing, calls `geo_localize()` on partner
5. **Distance Calculation**: Uses approximation formula for speed
6. **Price Setting**: Sets price_unit = distance × rate
7. **Price Lock**: Sets flag to prevent automatic recalculation

### Distance Formula
Uses a simplified distance approximation suitable for relatively short distances:

```python
def _approximate_distance(lat1, lon1, lat2, lon2):
    lat_diff_rad = (lat2 - lat1) * PI / 180
    lon_diff_rad = (lon2 - lon1) * PI / 180
    distance = EARTH_RADIUS_MILES * ((lat_diff_rad**2) + (lon_diff_rad**2))**0.5
    return distance
```

For more accurate long-distance calculations, consider implementing the Haversine formula.

## Error Handling

### Missing Customer
- **Trigger**: Delivery product added without selecting customer
- **Action**: Warning popup asking to select customer first

### Missing Coordinates
- **Trigger**: Customer has no GPS coordinates
- **Action**: Automatic geocoding attempt using `geo_localize()`

### Geocoding Failure
- **Trigger**: Address cannot be geocoded
- **Action**: UserError with instructions to verify address completeness:
  - Street address
  - City
  - State/Province
  - ZIP/Postal code
  - Country

### Invalid Address
- **Trigger**: Geocoding fails due to invalid/incomplete address
- **Action**: UserError with helpful guidance

## Fields Added

### res.partner
- `x_partner_distance` (Float): Stores calculated distance in miles

### sale.order.line
- `is_delivery_line` (Boolean, computed): Identifies delivery product lines
- `delivery_cost_calculated` (Boolean): Flag to prevent recalculation

## Logging

The module provides comprehensive logging:
- **INFO**: Successful operations (geocoding, calculations)
- **WARNING**: Handled issues (missing customer, skipped calculations)
- **ERROR**: Failures (geocoding errors, unexpected exceptions)

View logs in Odoo's standard logging output.

## Technical Details

### Dependencies
- `sale`: Sales management module
- `base_geolocalize`: GPS geocoding functionality

### Models Extended
- `res.partner`: Distance calculation methods
- `sale.order.line`: Delivery line detection and cost calculation
- `sale.order`: Manual recalculation action

### Key Methods

**res.partner:**
- `calculate_distance_from_origin()`: Main calculation logic
- `_approximate_distance()`: Distance formula
- `_display_address()`: Address formatting helper

**sale.order.line:**
- `_compute_is_delivery_line()`: Identifies delivery lines
- `_onchange_product_delivery_cost()`: Triggers on product selection
- `create()`: Handles programmatic line creation

**sale.order:**
- `action_recalculate_delivery_cost()`: Manual recalculation
- `_get_delivery_cost_info()`: Helper to get delivery info

## Troubleshooting

### Delivery cost not calculating
1. Verify "Delivery" product exists and is active
2. Confirm product type is "service"
3. Check product name exactly matches (case-insensitive)
4. Ensure customer is selected
5. Review logs for error messages

### Geocoding fails
1. Verify customer has complete address
2. Check all required fields are filled:
   - Street
   - City
   - State
   - ZIP
   - Country
3. Test `geo_localize()` manually on partner
4. Verify `base_geolocalize` module is installed

### Price keeps recalculating
- This shouldn't happen - price is locked by `delivery_cost_calculated` flag
- Check if flag is being reset elsewhere in customizations
- Review logs for unexpected recalculations

## Upgrading

When upgrading to more accurate distance calculations (e.g., Haversine):
1. Update `_approximate_distance()` method in `res_partner.py`
2. Optionally trigger recalculation for all existing orders
3. Test with known distances to verify accuracy

## License
LGPL-3

## Support
For issues or questions, contact your system administrator or module developer.

## Version History
- **17.0.1.0.0**: Initial release
  - Automatic delivery cost calculation
  - GPS geocoding integration
  - Price locking mechanism
  - Manual recalculation feature
  - Comprehensive error handling
