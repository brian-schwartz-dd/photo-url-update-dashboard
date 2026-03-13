# Photo URL Update Dashboard

Automated dashboard for managing photo URL updates from BSKU to catalog.

## Features

✅ **Merchant Selection** - Select one or more business IDs to monitor
✅ **Auto-Detection** - Automatically finds pending photo updates by comparing BSKU vs catalog timestamps
✅ **Multi-File Export** - Automatically splits large exports into files ≤45,001 rows
✅ **ZIP Download** - Downloads multiple files as a single ZIP
✅ **Smart Filtering** - Only shows items where BSKU is newer than catalog

---

## Quick Start (5 minutes)

### Prerequisites

- Python 3.8+ installed on your machine
- Access to DoorDash Snowflake (PRODDB)
- A Snowflake PAT token (see step 3 below)

### 1. Clone the Repository

```bash
git clone https://github.com/brian-schwartz-dd/photo-url-update-dashboard.git
cd photo-url-update-dashboard
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install streamlit snowflake-connector-python pandas
```

### 3. Get Your Snowflake PAT Token

You need a Personal Access Token (PAT) to connect to Snowflake:

1. Go to the **Data Tools PAT Generator** (ask your team for the link, or search Slack for "PAT generator")
2. Generate a new PAT token
3. **Copy the token** - you'll need it in the next step

### 4. Create Your Secrets File

Create a file named `.streamlit/secrets.toml` in the project directory:

```bash
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
[snowflake]
user = "FIRSTNAME.LASTNAME"
password = "your_PAT_token_here"
account = "doordash"
warehouse = "ADHOC"
database = "PRODDB"
schema = "static"
EOF
```

**Important:** Replace the values:
- `user` = Your Snowflake username (e.g., `BRIAN.SCHWARTZ`)
- `password` = The PAT token you generated in step 3
- `warehouse` = Use `ADHOC` or your team's warehouse name

**Example:**
```toml
[snowflake]
user = "BRIAN.SCHWARTZ"
password = "ghp_abc123xyz456..."
account = "doordash"
warehouse = "ADHOC"
database = "PRODDB"
schema = "static"
```

### 5. Run the Dashboard

```bash
streamlit run photo_update_dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

That's it! You're ready to use the dashboard.

---

## Daily Workflow

### Step 1: Open Dashboard
```bash
streamlit run photo_update_dashboard.py
```

### Step 2: Select Merchants
- Use the sidebar to select which business IDs to check
- Or add custom business IDs in the text area (one per line)
- **Optional**: Enter specific MSIDs to search for (one per line) - useful for batch lookups
- Click "Refresh Data" to get latest updates

### Step 3: Review Pending Updates
- View the count of pending updates
- See breakdown by NEW_ITEM vs URL_CHANGED
- Filter by change type or merchant if needed

### Step 4: Download CSV
- Click "Download CSV" (single file) or "Download ZIP" (multiple files)
- Files are automatically formatted for bulk upload:
  - Headers: `businessId, itemMerchantSuppliedId, URL, angle, source`
  - angle is always "FRONT", source is always "MX"
  - Max 45,001 rows per file
  - Ready to upload directly

### Step 5: Upload to Bulk Tool
- Upload the downloaded CSV/ZIP to your bulk upload tool
- Wait for processing to complete
- Done! Items won't reappear unless BSKU updates again

## Dashboard Layout

### Main Dashboard
- **Metrics Row**: Total pending, New items, Changed URLs, Merchant count
- **Data Table**: All pending updates with BSKU and catalog timestamps
- **Filters**: Filter by change type and merchant
- **Download Section**: Export CSV/ZIP for bulk upload

### Sidebar
- **Merchant Selection**: Choose which merchants to monitor from dropdown
- **Custom Business IDs**: Add additional business IDs (one per line)
- **Search Specific MSIDs**: Filter by specific Merchant Supplied Item IDs (optional)
- **Refresh Button**: Reload latest data

## File Formats

- Single file: `photo_updates_YYYYMMDD_HHMMSS.csv`
- ZIP file: `photo_updates_YYYYMMDD_HHMMSS.zip`
- Parts in ZIP: `photo_updates_part1_of_3.csv`, `photo_updates_part2_of_3.csv`, etc.
- Format: `businessId, itemMerchantSuppliedId, URL, angle, source`

## Adding More Merchants

Edit `photo_update_dashboard.py` and update the `AVAILABLE_MERCHANTS` dictionary:

```python
AVAILABLE_MERCHANTS = {
    "13055333": "Wegmans",
    "15617137": "Merchant B",
    "12345678": "Merchant C",
}
```

## Troubleshooting

### "Connection error" or "Authentication failed"

**Check your credentials:**
1. Open `.streamlit/secrets.toml`
2. Verify your `user` is in format `FIRSTNAME.LASTNAME` (all caps)
3. Make sure you're using a **PAT token** as the password, not your regular password
4. Verify `account = "doordash"` (lowercase)
5. Verify `warehouse = "ADHOC"` or your team's warehouse name

**Generate a new PAT token:**
- Old tokens may expire - generate a fresh one from the Data Tools PAT generator

### "Please select at least one merchant"
- Make sure you've selected at least one business ID in the sidebar dropdown
- Or enter custom business IDs in the text area

### "No pending updates"
- This means catalog is up to date with BSKU!
- New updates will appear when BSKU timestamps are newer than catalog
- Try selecting different merchants or check back later

### Dashboard not refreshing
- Click the "Refresh Data" button in the sidebar
- Or close and restart the dashboard: `Ctrl+C` in terminal, then run `streamlit run photo_update_dashboard.py` again

### "Module not found" errors
- Make sure you installed all dependencies: `pip install -r requirements.txt`
- You may need to use `pip3` instead of `pip` depending on your Python setup

## How It Works

The dashboard compares photo URLs between two sources:
1. **BSKU (Source of Truth)**: `BASELINE_SKU.PUBLIC.BASELINE_SKU_LATEST`
   - Contains the authoritative photo URLs with `updated_at` timestamps
2. **Catalog (Current State)**: `x360.prod.merchant_catalog`
   - Contains currently published photo URLs with `updated_at` timestamps

**Detection Logic:**
- **NEW_ITEM**: Item exists in BSKU but not in catalog
- **URL_CHANGED**: URLs differ AND BSKU `updated_at` > catalog `updated_at`
- Items automatically disappear from the list after catalog is updated

## Support

**For setup issues:**
- Check the Troubleshooting section above
- Verify your Snowflake credentials in `.streamlit/secrets.toml`
- Make sure you're using a valid PAT token

**For questions about the dashboard:**
- Contact Brian Schwartz or your team's data lead
- Check the "How It Works" section below for technical details

**For Snowflake access issues:**
- Contact your data team or Snowflake admins
- Verify you have access to `PRODDB` database
