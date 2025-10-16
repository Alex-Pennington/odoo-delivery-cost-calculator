# Pre-Upload Checklist ✅

## Configuration Consistency Check - PASSED ✅

All configuration values have been verified and are now consistent across all files.

---

## Current Configuration Values

### 📍 Origin Coordinates
- **Latitude:** `38.48358903556404`
- **Longitude:** `-82.7803864690895`

### 💰 Pricing
- **Rate per Mile:** `$2.50`

### 📏 Distance Limits
- **Manual Orders (Max):** `75 miles`
- **Website Checkout (Max):** `60 miles`

### 📦 Order Limits
- **Max Order Quantity (Website):** `8 units`

---

## Files Verified ✅

### Python Files
- ✅ `models/res_partner.py`
  - Lines 11-14: DEFAULT_ORIGIN_LAT, DEFAULT_ORIGIN_LON, DEFAULT_RATE_PER_MILE, DEFAULT_MAX_DELIVERY_DISTANCE
  - Line 259: Example in docstring updated
  
- ✅ `models/sale_order.py`
  - Line 11: DEFAULT_RATE_PER_MILE = 2.5

- ✅ `models/delivery_carrier.py`
  - Lines 10-12: DEFAULT_RATE_PER_MILE, DEFAULT_MAX_DISTANCE_MILES, DEFAULT_MAX_ORDER_QUANTITY

- ✅ `models/res_config_settings.py`
  - Lines 13, 20, 28, 36: All default values updated

### XML Files
- ✅ `views/delivery_carrier_views.xml`
  - Lines 15-18: Configuration display updated

### Manifest
- ✅ `__manifest__.py`
  - Description updated with correct values
  - Settings view still commented out (XPath issues)

---

## Validation Results

### Code Errors
- ✅ **No Odoo-specific errors** (Pylance warnings about "odoo" import are expected in standalone development environment)
- ✅ **No syntax errors**
- ✅ **No XML structure errors**

### Consistency Check
- ✅ All origin coordinates match
- ✅ All rate per mile values match
- ✅ All distance limits properly defined
- ✅ Documentation matches code

---

## Known Issues (Non-Blocking)

### Settings UI Disabled
- **Status:** Settings view is commented out in `__manifest__.py`
- **Reason:** XPath selector issues preventing view inheritance
- **Impact:** Backend configuration via `ir.config_parameter` works fine
- **Workaround:** Use hardcoded defaults or manually edit system parameters
- **Future Fix:** Need to identify correct XPath for your Odoo instance

### Import Warnings (Expected)
- Pylance reports "Import odoo could not be resolved"
- **This is normal** - Odoo modules require Odoo runtime environment
- These will resolve when module is loaded in Odoo

---

## Module Features Ready for Testing

### ✅ Manual Sales Orders
- Automatic delivery cost calculation when "Delivery" product added
- GPS distance calculation with Haversine formula
- Auto-geocoding for customers without coordinates
- Comprehensive validation and error messages
- Manual recalculation button

### ✅ Website Checkout
- GPS Distance-Based Delivery carrier configured
- Availability rules:
  - Customer within 60 miles ✅
  - Order quantity < 8 units ✅
  - Valid geocodable address ✅
- Automatic price calculation
- Silently hides when unavailable

### ✅ Validation & Error Handling
- Coordinate validation (zeros, out of range, >1000)
- Distance validation (75-mile radius for manual orders)
- Geocoding failure handling
- Comprehensive logging

---

## Upgrade Instructions

### 1. Upload Module
```bash
# Module is ready to upload to Odoo
# Located at: c:\Users\rayve\OneDrive\Documents\PlatformIO\Projects\odoo_dist\delivery_cost_calculator
```

### 2. Upgrade in Odoo
1. Go to Apps menu
2. Remove "Apps" filter
3. Search for "Delivery Cost Calculator"
4. Click "Upgrade" button
5. Module should upgrade without errors

### 3. Verify Installation
- Check that no errors appear during upgrade
- Verify GPS delivery carrier exists (Inventory → Configuration → Delivery Methods)
- Test manual sales order with "Delivery" product
- Test website checkout (if website_sale_delivery installed)

---

## Testing Checklist

### Manual Sales Order Testing
- [ ] Create sales order with customer
- [ ] Add "Delivery" product
- [ ] Verify automatic cost calculation
- [ ] Check distance is within 75 miles
- [ ] Test "Recalculate Delivery Cost" button
- [ ] Test with customer beyond 75 miles (should error)
- [ ] Test with customer without address (should auto-geocode or error)

### Website Checkout Testing
- [ ] Add products to cart (< 8 units)
- [ ] Enter delivery address within 60 miles
- [ ] Verify "GPS Distance-Based Delivery" appears
- [ ] Verify correct price displayed
- [ ] Complete checkout
- [ ] Test with 8+ units (GPS carrier should hide)
- [ ] Test with address beyond 60 miles (GPS carrier should hide)

---

## Configuration Notes

### Changing Values After Upload
If you need to change configuration values after testing:

1. **Via Code (Current Method):**
   - Edit constants in `models/res_partner.py` and `models/delivery_carrier.py`
   - Upgrade module in Odoo

2. **Via Database (Advanced):**
   ```sql
   UPDATE ir_config_parameter 
   SET value = '2.5' 
   WHERE key = 'delivery_cost_calculator.rate_per_mile';
   ```

3. **Via Settings UI (Future):**
   - Once XPath issue resolved, enable settings view
   - Go to Sales → Configuration → Settings
   - Find "Delivery Cost Calculator" section

---

## GitHub Status

- **Repository:** Alex-Pennington/odoo-delivery-cost-calculator
- **Branch:** main
- **Last Commit:** "fix: Temporarily disable settings view"
- **Status:** Ready for new commit with consistent configuration

### Recommended Next Commit
```bash
git add .
git commit -m "feat: Update configuration to production values (38.483°, -82.780°, $2.50/mi, 75mi)"
git push origin main
```

---

## Summary

✅ **ALL SYSTEMS GO!** Your module is ready for upload and testing.

- All configuration values are consistent
- No blocking errors
- All features implemented
- Documentation up to date
- Settings UI disabled but non-blocking

**Next Step:** Upload the module to Odoo and run the upgrade!
