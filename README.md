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
- ✅ **NEW: Custom GPS delivery carrier for website checkout**
- ✅ **NEW: Smart availability rules (max 60 miles, max 8 units)**
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
3. The `delivery` module installed (for GPS carrier feature)
4. *Optional*: The `website_sale_delivery` module (for e-commerce integration)
5. Customer field `x_partner_distance` created on res.partner (Float type)

**Note**: The GPS delivery carrier will only work on website checkout if `website_sale_delivery` is installed. Without it, the module still works for manual sales orders.

### Customization
To modify default settings, edit the constants at the top of the model files:

**In `models/res_partner.py`:**
```python
ORIGIN_LAT = 38.3353600  # Origin latitude
ORIGIN_LON = -82.7815527  # Origin longitude
EARTH_RADIUS_MILES = 3959
```

**In `models/sale_order.py`:**
```python
RATE_PER_MILE = 3.0  # Delivery rate per mile
DELIVERY_PRODUCT_NAME = 'Delivery'  # Name of delivery product
```

**In `models/delivery_carrier.py`:**
```python
ORIGIN_LAT = 38.3353600  # Origin latitude
ORIGIN_LON = -82.7815527  # Origin longitude
RATE_PER_MILE = 3.0  # Delivery rate per mile
MAX_DISTANCE_MILES = 60.0  # Maximum delivery distance
MAX_ORDER_QUANTITY = 8  # Maximum order quantity for GPS delivery
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

#### GPS Distance-Based Delivery Carrier

A custom delivery carrier is automatically created for website checkout:

**Availability Rules:**
- ✅ Customer within 60 miles of origin
- ✅ Order quantity less than 8 units (physical products only)
- ✅ Valid geocodable address

**Behavior:**
- Appears as "GPS Distance-Based Delivery" in shipping options
- Shows calculated price based on exact distance
- Automatically recalculates when address/cart changes
- Silently hides if conditions not met (no error shown to customer)
- Works alongside existing delivery methods

**Example Checkout Flow:**
1. Customer enters shipping address
2. Odoo geocodes address (if needed)
3. Calculates distance from origin
4. Checks availability rules
5. If available: Shows "GPS Distance-Based Delivery - $XX.XX"
6. Customer selects and completes checkout

## How It Works

### Workflow

1. **Product Detection**: Identifies "Delivery" product (service type, active)
2. **Customer Validation**: Ensures customer is selected
3. **GPS Check**: Verifies customer has coordinates
4. **Auto-Geocoding**: If missing, calls `geo_localize()` on partner
5. **Distance Calculation**: Uses approximation formula for speed
6. **Price Setting**: Sets price_unit = distance × rate
7. **Price Lock**: Sets flag to prevent automatic recalculation

### Website Checkout Workflow (GPS Carrier)

1. **Customer enters address** in checkout
2. **Address validation**: System geocodes if coordinates missing
3. **Availability check**: 
   - Calculate distance from origin
   - Count order quantity (physical products only)
   - Check constraints (≤60 miles, <8 units)
4. **Display shipping options**:
   - If available: Shows GPS carrier with calculated price
   - If not available: Carrier hidden, other methods shown
5. **Customer selects** shipping method
6. **Order creation**: Delivery price applied to order

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

- **Trigger**: Address cannot be geocoded
- **Action**: UserError with instructions to verify address completeness:
  - Street address
  - City
  - State/Province
  - ZIP/Postal code
  - Country

### GPS Carrier Not Available (Website Checkout)

- **Trigger**: Distance >60 miles OR quantity ≥8 units OR geocoding fails
- **Action**: Carrier silently hidden from shipping options (no error to customer)
- **User Experience**: Customer sees other available delivery methods only

## Fields Added

### res.partner
- `x_partner_distance` (Float): Stores calculated distance in miles

### sale.order.line

- `is_delivery_line` (Boolean, computed): Identifies delivery product lines
- `delivery_cost_calculated` (Boolean): Flag to prevent recalculation

### delivery.carrier

- `delivery_type` (Selection): Extends to include 'gps' option
- New carrier record: "GPS Distance-Based Delivery"

## Logging

The module provides comprehensive logging:
- **INFO**: Successful operations (geocoding, calculations)
- **WARNING**: Handled issues (missing customer, skipped calculations)
- **ERROR**: Failures (geocoding errors, unexpected exceptions)

View logs in Odoo's standard logging output.

## Technical Details

### Dependencies

- `sale`: Sales management module (required)
- `base_geolocalize`: GPS geocoding functionality (required)
- `delivery`: Delivery carrier management (required for GPS carrier)
- `website_sale_delivery`: E-commerce shipping integration (optional - for website checkout)

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

**delivery.carrier:**
- `gps_rate_shipment()`: Calculate shipping rate based on GPS distance
- `gps_send_shipping()`: Process shipment (mark as shipped)
- `gps_get_tracking_link()`: Return tracking link (returns False for local delivery)
- `gps_cancel_shipment()`: Cancel shipment

## Troubleshooting

### Delivery cost not calculating

1. Verify "Delivery" product exists and is active
2. Confirm product type is "service"
3. Check product name exactly matches (case-insensitive)
4. Ensure customer is selected
5. Review logs for error messages

### GPS carrier not appearing in website checkout

1. **Check distance**: Customer must be within 60 miles
   - View partner record → check `x_partner_distance` field
   - Manually calculate: Is address within 60 miles of origin?
2. **Check quantity**: Order must have less than 8 units
   - Review cart items
   - Only physical products (type='product' or 'consu') count
3. **Check address**: Must be valid and geocodable
   - Open partner in Odoo
   - Verify GPS coordinates populated
   - Try manual geocoding: Click "Geo Localize" button
4. **Check carrier**: Ensure GPS carrier is active
   - Go to Inventory → Configuration → Delivery Methods
   - Find "GPS Distance-Based Delivery"
   - Ensure "Website Published" is checked
5. **Check module**: Verify dependencies installed
   - `delivery` module installed
   - `website_sale_delivery` module installed
6. **Check logs**: Review Odoo logs for "GPS delivery" messages

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

### GPS carrier shows for orders over 60 miles

- Check `MAX_DISTANCE_MILES` constant in `models/delivery_carrier.py`
- Verify partner's `x_partner_distance` field is calculated correctly
- Review logs for distance calculation messages

### All orders show GPS carrier regardless of quantity

- Check `MAX_ORDER_QUANTITY` constant in `models/delivery_carrier.py`
- Verify quantity calculation includes only physical products
- Check for service products incorrectly typed as 'product'

## Upgrading

### From v17.0.2.x to v17.0.3.0 (Haversine Formula Update)

**Important**: Version 17.0.3.0 replaces the inaccurate flat-Earth distance approximation with the accurate Haversine formula. This will affect distance calculations.

**What Changed:**
- Old formula was significantly inaccurate (could be 2-3x off)
- New Haversine formula provides accurate great-circle distances
- Example: Location that was calculated as 12.76 miles now correctly shows as ~12.26 miles

**Impact:**
- All future distance calculations will be accurate
- Existing stored distances in `x_partner_distance` may be inaccurate
- Delivery costs will be recalculated next time customer places order

**Recommended Actions After Upgrade:**

1. **Clear existing distances** (forces recalculation):
   ```sql
   UPDATE res_partner SET x_partner_distance = NULL;
   ```

2. **Or recalculate for active customers** (Python):
   ```python
   # In Odoo shell or via developer console
   partners = env['res.partner'].search([('x_partner_distance', '>', 0)])
   for partner in partners:
       try:
           partner.calculate_distance_from_origin()
       except:
           pass  # Skip partners with invalid addresses
   ```

3. **Test with known locations** to verify accuracy against Google Maps

**No action required** if you're okay with distances being recalculated on next order.

---

## Upgrading to More Accurate Distance

If you need even more accuracy (accounting for roads, traffic, etc.):
1. Integrate with Google Maps Distance Matrix API
2. Update `_haversine_distance()` method in `res_partner.py`
3. Add API key configuration
4. Test with known distances to verify accuracy

## License
LGPL-3

## Support
For issues or questions, contact your system administrator or module developer.

## Version History

- **17.0.3.0.0**: Accurate Haversine Distance Formula
  - **BREAKING**: Replaced inaccurate flat-Earth approximation with Haversine formula
  - Significantly improved distance calculation accuracy
  - Example: Old formula calculated 12.76 miles, new formula correctly calculates ~12.26 miles
  - Added proper error handling for distance calculations
  - Removed unused PI constant
  - Existing partner distances may need recalculation
  - See "Upgrading" section for migration instructions

- **17.0.2.0.0**: GPS Delivery Carrier Feature
  - Added custom GPS delivery carrier for website checkout
  - Smart availability rules (max 60 miles, max 8 units)
  - Integration with Odoo delivery/website_sale_delivery modules
  - Comprehensive logging for carrier availability checks
  - Configuration view in delivery carrier form

- **17.0.1.0.1**: Bug Fixes
  - Fixed _display_address() conflict with Odoo core method
  - Fixed website_published field dependency issue

- **17.0.1.0.0**: Initial release
  - Automatic delivery cost calculation
  - GPS geocoding integration
  - Price locking mechanism
  - Manual recalculation feature
  - Comprehensive error handling
