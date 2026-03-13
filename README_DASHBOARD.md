# Photo URL Update Dashboard

Automated dashboard for managing photo URL updates from BSKU to catalog.

## Features

✅ **Merchant Selection** - Select one or more business IDs to monitor
✅ **Auto-Detection** - Automatically finds pending photo updates by comparing BSKU vs catalog timestamps
✅ **Multi-File Export** - Automatically splits large exports into files ≤45,001 rows
✅ **ZIP Download** - Downloads multiple files as a single ZIP
✅ **Smart Filtering** - Only shows items where BSKU is newer than catalog

## Setup Instructions

### 1. Install Dependencies

```bash
pip install streamlit snowflake-connector-python pandas
```

### 2. Configure Snowflake Credentials

Edit the file: `.streamlit/secrets.toml`

```toml
[snowflake]
user = "your_username"
password = "your_password"
account = "your_account"       # e.g., "abc12345.us-east-1"
warehouse = "your_warehouse"   # e.g., "COMPUTE_WH"
database = "proddb"
schema = "static"
```

### 3. Run the Dashboard

```bash
streamlit run photo_update_dashboard.py
```

The dashboard will open automatically in your browser at `http://localhost:8501`

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

### "Please select at least one merchant"
- Make sure you've selected at least one business ID in the sidebar

### "Connection error"
- Check your `.streamlit/secrets.toml` credentials
- Verify you have access to the Snowflake database

### "No pending updates"
- This means catalog is up to date with BSKU!
- New updates will appear when BSKU timestamps are newer than catalog

### Dashboard not refreshing
- Click the "Refresh Data" button in the sidebar
- Or close and restart the dashboard

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

For issues or questions, contact your data team.
