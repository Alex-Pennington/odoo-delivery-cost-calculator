# Troubleshooting Guide

## Common Issues and Solutions

### Issue: `column res_partner.x_partner_distance does not exist`

**Symptoms:**
- Odoo UI completely locked up
- Error: `psycopg2.errors.UndefinedColumn: column res_partner.x_partner_distance does not exist`
- Cannot access any views or settings

**Root Cause:**
The module references a custom field `x_partner_distance` that doesn't exist in the database column. This happens when:
- Module is installed in a fresh database
- Field definition exists in code but database column wasn't created
- Custom field was removed from database but code still references it

**Solution 1: Upgrade Module (Recommended)**
```bash
# In Odoo UI (if accessible)
Apps → Delivery Cost Calculator → Upgrade

# This will create the field automatically
```

**Solution 2: Direct Database Fix**
If UI is locked and you can't upgrade:

```bash
# Find your database name
docker exec -it <postgres_container_id> psql -U odoo -d postgres -c "\l"

# Add the missing column (replace 'oe' with your database name)
docker exec -it <postgres_container_id> psql -U odoo -d oe -c "ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS x_partner_distance NUMERIC(10,2) DEFAULT 0.0;"

# Restart Odoo
docker restart <odoo_container_id>
```

**Solution 3: Using Odoo Shell**
```bash
# Enter Odoo shell
docker exec -it <odoo_container_id> odoo shell -d oe

# In the shell:
env['ir.model.fields'].create({
    'name': 'x_partner_distance',
    'field_description': 'Distance from Origin (miles)',
    'model_id': env.ref('base.model_res_partner').id,
    'ttype': 'float',
    'state': 'manual',
})
```

---

### Issue: Invalid GPS Coordinates (0, 0) or Large Numbers

**Symptoms:**
- Error: "Coordinates are zero or empty"
- Error: "Coordinates are impossibly large"
- Distance calculation fails

**Root Cause:**
Geocoding service returned bad data or address is invalid.

**Solution:**
1. Verify customer address is complete:
   - Street address
   - City
   - State/Province
   - ZIP/Postal code
   - Country

2. Try manual geocoding:
   - Open partner record
   - Click "Geo Localize" button
   - Check if latitude/longitude are populated correctly

3. If coordinates are still wrong, manually set them:
   - Find correct coordinates using Google Maps
   - Update `Latitude` and `Longitude` fields on partner

---

### Issue: Delivery Not Available (Distance > 100 Miles)

**Symptoms:**
- Error: "Customer location is X miles from origin. Maximum delivery distance: 100 miles"
- Cannot add delivery to order

**Root Cause:**
Customer is outside the configured delivery radius.

**Solution:**
1. Check if customer address is correct
2. If legitimate customer, adjust settings:
   - Go to: **Sales → Configuration → Settings**
   - Scroll to **GPS Delivery Cost Calculator**
   - Increase **Maximum Delivery Distance** (e.g., from 100 to 150 miles)
   - Click **Save**

---

### Issue: GPS Carrier Not Showing on Website Checkout

**Symptoms:**
- GPS delivery option doesn't appear during checkout
- Other shipping methods work fine

**Root Cause:**
Order doesn't meet GPS carrier availability criteria.

**Solution:**
Check these conditions:
1. **Distance**: Customer must be within GPS Carrier Max Distance (default: 60 miles)
2. **Quantity**: Order must have less than Max Order Quantity (default: 8 units)
3. **Address**: Customer must have valid geocodable address

To adjust limits:
- Go to: **Sales → Configuration → Settings**
- Scroll to **GPS Delivery Cost Calculator**
- Adjust **GPS Carrier Max Distance** or **Maximum Order Quantity**
- Click **Save**

---

### Issue: Settings Not Appearing in Sales Configuration

**Symptoms:**
- Cannot find "GPS Delivery Cost Calculator" in Settings page
- Settings page loads but section is missing

**Root Cause:**
- Module not properly installed/upgraded
- View not loading correctly

**Solution:**
```bash
# Upgrade the module with update of views
Apps → Delivery Cost Calculator → Upgrade

# Or via command line:
docker exec -it <odoo_container_id> odoo -d oe -u delivery_cost_calculator

# Clear browser cache and refresh
Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
```

---

### Issue: Rate Per Mile Not Updating

**Symptoms:**
- Changed rate in settings but orders still use old rate
- Price calculations seem wrong

**Root Cause:**
Existing delivery lines have locked prices (by design).

**Solution:**
This is expected behavior for price locking. To update:

1. **For new orders**: New rate applies automatically
2. **For existing orders**: 
   - Open order in draft/quotation state
   - Click **Recalculate Delivery Cost** button
   - This will recalculate using new rate

**Note**: Confirmed orders keep their original price (intentional).

---

### Issue: Module Won't Install/Upgrade

**Symptoms:**
- Error during installation
- Module shows as "To Install" but won't install

**Root Cause:**
- Missing dependencies
- Database migration issues
- Code syntax errors

**Solution:**
```bash
# Check Odoo logs
docker logs <odoo_container_id>

# Common fixes:

# 1. Update module list
Apps → Update Apps List

# 2. Install dependencies manually
Apps → Search for:
- Sales Management (sale)
- Geolocalize (base_geolocalize)
- Delivery Costs (delivery)

# 3. Force reinstall
docker exec -it <odoo_container_id> odoo -d oe -u delivery_cost_calculator --stop-after-init

# 4. Check for Python syntax errors in module files
```

---

## Debug Mode Tips

### Enable Developer Mode
1. Go to **Settings**
2. Scroll to bottom
3. Click **Activate the developer mode**

### Useful Debug Features:
- **View Metadata**: Bug icon in top-right of forms
- **Edit View**: See XML structure of current view
- **View Fields**: See all technical field names
- **Technical Menu**: Access to low-level configurations

---

## Database Commands Reference

### Finding Your Database Name
```bash
docker exec -it <postgres_container_id> psql -U odoo -d postgres -c "\l"
```

### Checking if Column Exists
```bash
docker exec -it <postgres_container_id> psql -U odoo -d oe -c "\d res_partner"
```

### Viewing Field Values
```bash
docker exec -it <postgres_container_id> psql -U odoo -d oe -c "SELECT id, name, x_partner_distance FROM res_partner WHERE x_partner_distance > 0 LIMIT 10;"
```

### Resetting Distance Values
```bash
docker exec -it <postgres_container_id> psql -U odoo -d oe -c "UPDATE res_partner SET x_partner_distance = 0.0;"
```

---

## Container Management

### Find Container IDs
```bash
# List all running containers
docker ps

# Find Odoo container
docker ps | grep odoo

# Find PostgreSQL container  
docker ps | grep postgres
```

### Restart Containers
```bash
# Restart Odoo
docker restart <odoo_container_id>

# Restart both Odoo and PostgreSQL
docker restart <odoo_container_id> <postgres_container_id>
```

### View Logs
```bash
# Follow Odoo logs in real-time
docker logs -f <odoo_container_id>

# View last 100 lines
docker logs --tail 100 <odoo_container_id>

# View PostgreSQL logs
docker logs <postgres_container_id>
```

---

## Support & Resources

### Documentation
- [README.md](README.md) - Main documentation
- [INSTALLATION.md](INSTALLATION.md) - Installation guide
- [MIGRATION.md](MIGRATION.md) - Upgrading from old versions
- [DATABASE_FIX.sql](DATABASE_FIX.sql) - SQL fixes for database issues

### Getting Help
1. Check Odoo logs: `docker logs <odoo_container_id>`
2. Enable Developer Mode and check View Metadata
3. Review this troubleshooting guide
4. Check GitHub issues: https://github.com/Alex-Pennington/odoo-delivery-cost-calculator

### Common Log Locations
- **Odoo logs**: Docker logs or `/var/log/odoo/odoo.log` (if mapped)
- **PostgreSQL logs**: Docker logs or `/var/log/postgresql/`
- **Module logs**: Search for `delivery_cost_calculator` in Odoo logs

---

## Prevention Best Practices

### Before Upgrading
1. **Backup database**: `docker exec <postgres_container_id> pg_dump -U odoo oe > backup.sql`
2. **Test in staging**: Try upgrade in test environment first
3. **Review changelog**: Check what changed in new version

### Regular Maintenance
1. **Monitor logs**: Watch for warnings/errors
2. **Test critical workflows**: Regularly test order creation with delivery
3. **Verify settings**: Periodically check GPS Delivery Cost Calculator settings
4. **Keep backups**: Regular database backups before changes

### Code Modifications
If you modify the module code:
1. **Test locally first**: Don't edit production directly
2. **Use Git**: Commit changes before deploying
3. **Update version**: Increment version in `__manifest__.py`
4. **Document changes**: Add notes to MIGRATION.md if needed
