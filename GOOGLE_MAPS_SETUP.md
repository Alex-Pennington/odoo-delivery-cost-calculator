# Google Maps API Setup Guide

## 🗺️ Overview

The Delivery Cost Calculator now supports **Google Maps Distance Matrix API** for accurate road-based distance calculations instead of straight-line distances.

### Why Use Google Maps API?

| Method | Accuracy | Cost | Best For |
|--------|----------|------|----------|
| **Haversine × 1.3** | ±10-20% | Free | Most cases, budget-conscious |
| **Google Maps API** | ±5% | ~$0.005/calc | High accuracy needs, professional quotes |

---

## 🚀 Quick Start

### Option 1: Use Road Multiplier (No Setup)
**Default behavior** - Already working!
- Uses: Straight-line distance × 1.3
- Accuracy: ~±15%
- Cost: Free
- Setup: None required

### Option 2: Enable Google Maps API
**Better accuracy** - Requires API key
- Uses: Real road routing
- Accuracy: ~±5%
- Cost: $5 per 1,000 calculations
- Setup: 10 minutes

---

## 📋 Google Maps API Setup

### Step 1: Create Google Cloud Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Accept terms of service
4. **You'll need a credit card** (but you get $200 free credit monthly)

### Step 2: Create a Project

1. Click the project dropdown (top left)
2. Click "**New Project**"
3. Name it: "Odoo Delivery Calculator"
4. Click "**Create**"

### Step 3: Enable Distance Matrix API

1. Go to **APIs & Services** → **Library**
2. Search for "**Distance Matrix API**"
3. Click on it
4. Click "**Enable**"

### Step 4: Create API Key

1. Go to **APIs & Services** → **Credentials**
2. Click "**+ Create Credentials**" → "**API Key**"
3. Copy the API key (starts with `AIza...`)
4. Click "**Restrict Key**" (recommended for security)

### Step 5: Restrict API Key (Recommended)

1. Under "**API restrictions**":
   - Select "**Restrict key**"
   - Check only "**Distance Matrix API**"
2. Under "**Application restrictions**" (optional):

   - Select "**IP addresses**"
   - Add your Odoo server's IP address
3. Click "**Save**"

### Step 6: Enable Billing

1. Go to **Billing** in left menu
2. Link a payment method
3. **Don't worry**: You get $200 free credit/month
4. At $0.005 per calculation, that's **40,000 free calculations/month**!

---

## ⚙️ Configure in Odoo

### Method 1: Via Settings UI (Once Enabled)

1. Go to **Settings** → Click "**Sales**" in left sidebar
2. Scroll to "**GPS Delivery Cost Calculator**" section
3. Enter your API key in "**Google Maps API Key**" field
4. Check "**Use Google Maps for Distance**"
5. Click "**Save**"

### Method 2: Via Database (Quick)

```bash
docker exec -it 7b2756cb1d4e psql -U odoo -d oe
```

```sql
-- Set your API key
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
VALUES (
    'delivery_cost_calculator.google_api_key', 
    'YOUR_API_KEY_HERE',
    NOW(), NOW(), 1, 1
)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

-- Enable Google Maps
INSERT INTO ir_config_parameter (key, value, create_date, write_date, create_uid, write_uid)
VALUES (
    'delivery_cost_calculator.use_google_maps', 
    'True',
    NOW(), NOW(), 1, 1
)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;

\q
```

---

## 💰 Cost Breakdown

### Google Maps Pricing

- **First 40,000 calls/month**: FREE ($200 credit)
- **After 40,000**: $0.005 per call ($5 per 1,000)

### Usage Examples

| Your Volume | Monthly Cost | Cost per Order |
|-------------|--------------|----------------|
| 100 orders/month | $0.00 (free) | $0.00 |
| 1,000 orders/month | $0.00 (free) | $0.00 |
| 10,000 orders/month | $0.00 (free) | $0.00 |
| 50,000 orders/month | $50.00 | $0.001 |
| 100,000 orders/month | $300.00 | $0.003 |

**Note**: Each order calculates distance once, not per page view.

---

## 🔍 How It Works

### Without Google Maps (Default)
```
Customer Address
    ↓ (geocode to GPS)
GPS Coordinates
    ↓ (Haversine formula)
Straight-line Distance: 10.5 miles
    ↓ (× road multiplier 1.3)
Estimated Road Distance: 13.65 miles
    ↓ (× $2.50/mile)
Delivery Cost: $34.13
```

### With Google Maps API
```
Customer Address
    ↓ (geocode to GPS)
GPS Coordinates
    ↓ (Google Maps API)
Actual Road Distance: 14.2 miles
    ↓ (× $2.50/mile)
Delivery Cost: $35.50
```

---

## 🛡️ Fallback Behavior

The module is **smart and resilient**:

1. **API key not configured** → Uses Haversine × multiplier
2. **API call fails** → Uses Haversine × multiplier  
3. **API quota exceeded** → Uses Haversine × multiplier
4. **Network timeout** → Uses Haversine × multiplier

**You'll never lose functionality!** The system always has a working fallback.

---

## 📊 Monitoring Usage

### Via Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** → **Dashboard**
4. Click "**Distance Matrix API**"
5. View usage charts and costs

### Set Up Budget Alerts

1. Go to **Billing** → **Budgets & alerts**
2. Click "**Create Budget**"
3. Set limit (e.g., $10/month)
4. Add your email for alerts
5. Click "**Finish**"

---

## 🧪 Testing

### Test Without Spending Money

```python
# Test with API disabled first
delivery_cost_calculator.use_google_maps = False
# Make test order, note distance

# Enable API
delivery_cost_calculator.use_google_maps = True
delivery_cost_calculator.google_api_key = 'YOUR_KEY'
# Make same order, compare distance

# Each test costs $0.005 (half a penny)
```

### Test Addresses

Use these to verify it's working:

| From | To | Haversine | Google Maps | Difference |
|------|-----|-----------|-------------|------------|
| Your origin | Same city | ~10 mi | ~12 mi | +20% |
| Your origin | 30 mi away | ~30 mi | ~35 mi | +17% |
| Your origin | 60 mi away | ~60 mi | ~68 mi | +13% |

---

## 🔧 Troubleshooting

### "Google Maps API key not configured"
- Check: API key entered in settings
- Check: No extra spaces in API key
- Solution: Copy/paste key directly from Google Cloud

### "Google Maps API error: REQUEST_DENIED"
- Check: Distance Matrix API is enabled
- Check: API key restrictions allow your IP
- Check: Billing is enabled on your Google account

### "Google Maps API error: OVER_QUERY_LIMIT"
- You've exceeded free tier (40,000/month)
- Solution: Disable Google Maps or increase budget
- Fallback: System automatically uses Haversine

### Distance seems wrong
- Verify origin coordinates are correct
- Check customer address is accurate
- Remember: Google uses fastest route, not shortest

---

## 📈 Performance Impact

| Setting | Speed | Accuracy |
|---------|-------|----------|
| Haversine only | Instant | ±30% |
| Haversine × 1.3 | Instant | ±15% |
| Google Maps API | 1-2 seconds | ±5% |

**Recommendation**: 
- Use Google Maps for **quote generation** (accuracy matters)
- Consider Haversine for **website checkout** (speed matters)
- Configure max distance limits to minimize API calls for out-of-range customers

---

## 🎯 Best Practices

### 1. Start with Fallback Mode
Test your module with Haversine × multiplier first. Once working, add Google Maps.

### 2. Adjust Road Multiplier by Region
- Urban areas with grid streets: **1.2**
- Mixed suburban/rural: **1.3** (default)
- Mountain/winding roads: **1.4**

### 3. Cache Distances (Future Enhancement)
Store calculated distances in customer record to avoid recalculating.

### 4. Monitor Costs
Set up Google Cloud budget alerts at $10, $25, $50.

### 5. Consider Hybrid Approach
- Use Google Maps for orders > $100
- Use Haversine for smaller orders
- Implement in `calculate_distance_from_origin()` with conditional logic

---

## 🔒 Security Best Practices

1. **Restrict API Key** to only Distance Matrix API
2. **Restrict by IP** to your Odoo server's address
3. **Never commit** API key to git
4. **Use environment variables** in production
5. **Rotate keys** periodically

---

## 📚 Additional Resources

- [Distance Matrix API Documentation](https://developers.google.com/maps/documentation/distance-matrix)
- [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)
- [API Key Best Practices](https://developers.google.com/maps/api-security-best-practices)

---

## ❓ FAQ

**Q: Do I need to enable Google Maps?**  
A: No! The module works great with Haversine × multiplier (free).

**Q: Will it work without an API key?**  
A: Yes! It automatically falls back to Haversine × road multiplier.

**Q: What if I run out of free credits?**  
A: You'll get charged, or set a budget limit to auto-disable at limit.

**Q: Can I switch back to Haversine?**  
A: Yes! Just uncheck "Use Google Maps" in settings.

**Q: Does it work offline?**  
A: Google Maps needs internet. Falls back to Haversine if offline.

**Q: Is my API key secure in Odoo?**  
A: Yes, stored in `ir_config_parameter` (not visible to regular users).

---

## 🎉 You're Ready!

Your delivery cost calculator now supports both methods:
- ✅ **Free**: Haversine × road multiplier (~85% accuracy)
- ✅ **Premium**: Google Maps API (~95% accuracy)

Choose what works best for your business! 🚚📦
