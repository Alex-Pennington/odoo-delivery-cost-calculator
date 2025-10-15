# GPS Delivery Carrier - Installation & Configuration Guide

## Quick Start

### 1. Update Module in Odoo

Since you already have the module installed, you need to **upgrade** it to get the new GPS carrier feature:

#### Option A: Via Odoo UI (Recommended)
1. Enable **Developer Mode**:
   - Settings → Activate the developer mode
   - OR add `?debug=1` to your URL
2. Go to **Apps**
3. Remove the "Apps" filter (click the X)
4. Search for "**Delivery Cost Calculator**"
5. Click the **⋮** menu → **Upgrade**
6. Wait for upgrade to complete

#### Option B: Via Docker Command Line
```bash
# Replace with your actual container and database names
docker exec -it <odoo_container> odoo -u delivery_cost_calculator -d <database_name> --stop-after-init
docker restart <odoo_container>
```

### 2. Verify Installation

After upgrading, check:
1. Go to **Inventory → Configuration → Delivery Methods**
2. You should see: **"GPS Distance-Based Delivery"**
3. Click on it to view details
4. Ensure **"Website Published"** is checked ✓

### 3. Test on Website Checkout

1. Go to your e-commerce website
2. Add products to cart (less than 8 units)
3. Proceed to checkout
4. Enter a shipping address within 60 miles
5. You should see **"GPS Distance-Based Delivery - $XX.XX"** as an option

---

## Detailed Configuration

### Constants (Customize if Needed)

Edit `models/delivery_carrier.py`:

```python
ORIGIN_LAT = 38.3353600         # Your warehouse/origin latitude
ORIGIN_LON = -82.7815527         # Your warehouse/origin longitude
RATE_PER_MILE = 3.0              # Price per mile
MAX_DISTANCE_MILES = 60.0        # Maximum delivery distance
MAX_ORDER_QUANTITY = 8           # Maximum order quantity for this method
```

### Carrier Settings

In Odoo UI (Inventory → Configuration → Delivery Methods → GPS Distance-Based Delivery):

- **Name**: GPS Distance-Based Delivery (customize as desired)
- **Delivery Type**: GPS Distance Based
- **Website Published**: ✓ (must be checked for website visibility)
- **Sequence**: 5 (controls display order in checkout)
- **Company**: Your company

---

## How It Works

### Availability Rules

The GPS carrier **only appears** when ALL conditions are met:

1. ✅ **Distance**: Customer within 60 miles of origin
2. ✅ **Quantity**: Order has less than 8 physical product units
3. ✅ **Address**: Valid, geocodable shipping address

If ANY condition fails → carrier is **silently hidden** (no error to customer).

### Calculation Process

1. Customer enters shipping address at checkout
2. System checks if address has GPS coordinates
3. If missing → automatically calls `geo_localize()` to get coordinates
4. Calculates distance using approximation formula
5. Checks distance ≤ 60 miles
6. Counts physical products in cart
7. Checks quantity < 8 units
8. If both pass → displays carrier with calculated price
9. If either fails → hides carrier, shows other methods

### Price Calculation

```
Shipping Cost = Distance (miles) × $3.00
```

Example:
- Customer 15.5 miles away
- Shipping cost = 15.5 × $3.00 = **$46.50**

---

## Troubleshooting

### GPS Carrier Not Appearing

#### Check Distance
```
1. Open customer record in Odoo
2. Look for "Distance from Origin" field
3. Is it <= 60 miles?
4. If field is empty, manually click "Geo Localize" button
```

#### Check Quantity
```
1. Review cart items
2. Count total quantity of physical products
3. Service products (type='service') are NOT counted
4. Is total < 8 units?
```

#### Check Address
```
1. Ensure customer has complete address:
   - Street
   - City
   - State
   - ZIP
   - Country
2. Try manual geocoding on partner record
3. Check if coordinates appear after geocoding
```

#### Check Carrier Status
```
1. Go to: Inventory → Configuration → Delivery Methods
2. Find: GPS Distance-Based Delivery
3. Verify:
   ✓ Website Published = True
   ✓ Delivery Type = "GPS Distance Based"
   ✓ Active (not archived)
```

#### Check Module Dependencies
```
1. Go to Apps
2. Search for "delivery" → ensure installed
3. Search for "website_sale_delivery" → ensure installed
4. If either missing, install them
5. Upgrade delivery_cost_calculator module
```

### Debug Logging

Check Odoo logs for "GPS delivery" messages:

```bash
# View logs in Docker
docker logs -f <odoo_container> | grep "GPS delivery"
```

Log messages include:
- `GPS delivery available`: Carrier shown, with distance and price
- `GPS delivery unavailable`: Carrier hidden, with reason
- `GPS delivery check`: Availability check details

---

## Testing Checklist

- [ ] **Close customer (<8 units)**: Carrier appears with correct price
- [ ] **Close customer (≥8 units)**: Carrier hidden
- [ ] **Distant customer (>60 mi, <8 units)**: Carrier hidden
- [ ] **Customer without GPS**: Auto-geocodes, then applies rules
- [ ] **Invalid address**: Carrier hidden (no error)
- [ ] **Change address in checkout**: Carrier recalculates/hides as needed
- [ ] **Existing carriers**: All other methods still work
- [ ] **Price accuracy**: Manual calculation matches displayed price

---

## Integration with Existing Methods

### Your Current Carriers

You mentioned these existing delivery methods:
- 10 Mile Delivery (Based on Rules)
- 20 Mile Delivery (Based on Rules)  
- 30 Mile Delivery (Based on Rules)
- On Site Pickup (Based on Rules)

### How GPS Carrier Fits In

The GPS carrier **adds** to your existing methods, doesn't replace them:

**Scenario 1**: Customer 15 miles away, 5 units
- ✅ GPS Distance-Based Delivery: $45.00 (15 × $3)
- ✅ 10 Mile Delivery: (your rate)
- ✅ 20 Mile Delivery: (your rate)
- ✅ 30 Mile Delivery: (your rate)
- ✅ On Site Pickup: (your rate)
- Customer chooses cheapest/preferred option

**Scenario 2**: Customer 15 miles away, 10 units (over limit)
- ❌ GPS Distance-Based Delivery: Hidden
- ✅ 10 Mile Delivery: (your rate)
- ✅ 20 Mile Delivery: (your rate)
- ✅ 30 Mile Delivery: (your rate)
- ✅ On Site Pickup: (your rate)
- Customer sees other 4 options

**Scenario 3**: Customer 75 miles away, 5 units (over distance)
- ❌ GPS Distance-Based Delivery: Hidden
- ❌ 10/20/30 Mile Delivery: Likely hidden by your rules
- ✅ On Site Pickup: Available
- Customer sees only pickup option

### Display Order

Control display order with **Sequence** field:
```
Sequence 1: Displays first
Sequence 5: GPS carrier (middle)
Sequence 10: Displays last
```

Adjust in: Delivery Methods → GPS Distance-Based Delivery → Sequence

---

## Advanced Customization

### Change Maximum Distance

Edit `models/delivery_carrier.py`:
```python
MAX_DISTANCE_MILES = 100.0  # Change from 60 to 100 miles
```

### Change Maximum Quantity

```python
MAX_ORDER_QUANTITY = 15  # Change from 8 to 15 units
```

### Change Rate

```python
RATE_PER_MILE = 2.50  # Change from $3.00 to $2.50
```

### Change Origin Point

```python
ORIGIN_LAT = 40.7128  # New York City example
ORIGIN_LON = -74.0060
```

**After changes**: Upgrade module again for changes to take effect.

### More Accurate Distance Formula

The current formula is a rough approximation. For better accuracy over longer distances, you can implement the Haversine formula in `res_partner.py` `_approximate_distance()` method.

---

## Support

**Module Version**: 17.0.2.0.0  
**GitHub**: https://github.com/Alex-Pennington/odoo-delivery-cost-calculator  
**Odoo Version**: 17.0

For issues:
1. Check troubleshooting section above
2. Review Odoo logs for error messages
3. Verify all prerequisites installed
4. Check GitHub issues for similar problems

---

## FAQ

**Q: Can I have multiple GPS carriers with different rates?**  
A: Yes, duplicate the carrier record and modify the rate in Python constants. You'll need to create separate delivery types or use price rules.

**Q: Does this work with international addresses?**  
A: Yes, as long as the address can be geocoded. However, the distance formula is most accurate for shorter distances.

**Q: Will this slow down my checkout?**  
A: No. If customer already has GPS coordinates, calculation is instant. First-time geocoding adds ~1-2 seconds.

**Q: What happens if geocoding fails?**  
A: The carrier silently hides. Customer sees other available methods. No error is shown to maintain smooth UX.

**Q: Can I show a message when the carrier is hidden?**  
A: Not by default (to avoid confusing customers), but you can customize the code to add a notification when rules aren't met.

**Q: Does this affect my existing delivery product?**  
A: No. The GPS carrier uses Odoo's default delivery product. Your existing "Delivery" product in sales orders is separate.

**Q: Can I restrict by customer type or tags?**  
A: Yes, you can add additional checks in the `gps_rate_shipment()` method to filter by customer attributes.

---

## Version History

**v17.0.2.0.0** (Current)
- Added GPS delivery carrier for website checkout
- Smart availability rules (distance and quantity)
- Production-ready with comprehensive logging

**v17.0.1.0.0**
- Initial release with manual delivery cost calculation
