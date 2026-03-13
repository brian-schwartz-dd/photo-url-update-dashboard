# Photo URL Update Dashboard - User Guide

**Complete step-by-step instructions for setting up and using the Photo URL Update Dashboard**

---

## Overview

This dashboard helps you identify and export photo URL updates that need to be synced from BSKU to the merchant catalog. It automatically detects items where BSKU has newer photos than what's published in the catalog.

### Complete Workflow

The dashboard supports a complete end-to-end workflow:

1. **Detect updates** - Dashboard finds items where BSKU has newer photos than catalog
2. **Export URLs** - Download photo URLs that need processing
3. **Create photo IDs** - Upload URLs to photo creation tool (external)
4. **Process output** - Upload photo ID results back to dashboard
5. **Catalog update** - Download catalog-ready files and upload to catalog tool

**Time estimate:** 15-30 minutes depending on number of items

---

## Part 1: One-Time Setup (15 minutes)

### Step 1: Get the Code from GitHub

1. **Open your terminal** (Mac: Terminal app, Windows: Command Prompt or PowerShell)

2. **Navigate to where you want to install the dashboard:**
   ```bash
   cd ~/Documents
   ```
   (You can choose any folder you like)

3. **Clone the repository from GitHub:**
   ```bash
   git clone https://github.com/brian-schwartz-dd/photo-url-update-dashboard.git
   ```

4. **Go into the new folder:**
   ```bash
   cd photo-url-update-dashboard
   ```

You now have all the dashboard code on your computer!

---

### Step 2: Install Python Dependencies

**Install the required Python packages:**

```bash
pip install -r requirements.txt
```

If that doesn't work, try:
```bash
pip3 install -r requirements.txt
```

**What this does:** Installs Streamlit (the dashboard framework), Snowflake connector, and Pandas (data handling).

---

### Step 3: Get Your Snowflake Access Information

You need these pieces of information to connect to Snowflake:

#### A. Your Snowflake Username
- Format: `FIRSTNAME.LASTNAME` (all uppercase)
- Example: If your email is `john.doe@doordash.com`, your username is `JOHN.DOE`

#### B. Your Snowflake PAT Token

**What is a PAT token?** A Personal Access Token - it's like a password for connecting to Snowflake from apps.

**How to get it:**
1. Search in Slack for "PAT generator" or "Data Tools PAT"
2. Ask your team: "Where's the Snowflake PAT generator?"
3. Once you find it, click "Generate new token"
4. Give it a name like "photo-dashboard"
5. Set expiration (90 days is typical)
6. **Copy the entire token** - it will look like `ghp_abc123xyz...` (very long)
7. Save it somewhere temporarily - you'll need it in the next step

**Can't find the PAT generator?** Ask your manager or a teammate where to get Snowflake PAT tokens.

#### C. Your Warehouse Name

Most users should use: **`ADHOC`**

If your team has a specific warehouse, your manager can tell you which one to use.

---

### Step 4: Create Your Configuration File

**Create a secrets file with your Snowflake credentials:**

1. **Make sure you're in the dashboard folder:**
   ```bash
   cd ~/Documents/photo-url-update-dashboard
   ```

2. **Create the secrets directory:**
   ```bash
   mkdir -p .streamlit
   ```

3. **Create the secrets file:**

   **On Mac/Linux:**
   ```bash
   nano .streamlit/secrets.toml
   ```

   **On Windows:**
   ```bash
   notepad .streamlit\secrets.toml
   ```

4. **Paste this into the file:**
   ```toml
   [snowflake]
   user = "YOUR.USERNAME"
   password = "your_PAT_token_here"
   account = "doordash"
   warehouse = "ADHOC"
   database = "PRODDB"
   schema = "static"
   ```

5. **Replace the placeholder values:**
   - `user` = Your Snowflake username (e.g., `JOHN.DOE`)
   - `password` = The PAT token you copied in Step 3B

   **Example:**
   ```toml
   [snowflake]
   user = "JOHN.DOE"
   password = "ghp_abc123xyz456789..."
   account = "doordash"
   warehouse = "ADHOC"
   database = "PRODDB"
   schema = "static"
   ```

6. **Save the file:**
   - In nano: Press `Ctrl+O`, then `Enter`, then `Ctrl+X`
   - In notepad: Click File → Save

---

### Step 5: Test the Dashboard

**Run the dashboard for the first time:**

```bash
streamlit run photo_update_dashboard.py
```

**What should happen:**
- Your web browser should automatically open to `http://localhost:8501`
- You should see the Photo URL Update Dashboard

**If you see an error:**
- Check the [Troubleshooting section](#troubleshooting) below
- Most common issue: incorrect username or PAT token format

---

## Part 2: Using the Dashboard (Daily Workflow)

### Step 1: Start the Dashboard

**Open your terminal and run:**

```bash
cd ~/Documents/photo-url-update-dashboard
streamlit run photo_update_dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

### Step 2: Select Merchants to Monitor

**In the sidebar (left side of the screen):**

1. **Use the dropdown menu** to select one or more merchants
   - Example: Select "13055333 - Wegmans"
   - You can select multiple merchants by clicking several

2. **OR add custom Business IDs:**
   - Scroll down to "Add Custom Business IDs"
   - Enter business IDs, one per line
   - Example:
     ```
     13055333
     12345678
     ```

3. **OPTIONAL - Search specific items:**
   - If you want to look up specific items only
   - Scroll to "Search Specific MSIDs (Optional)"
   - Enter Merchant Supplied Item IDs, one per line
   - Leave blank to see all items

4. **OPTIONAL - Filter by date:**
   - **BSKU Updated:** Filter items by when BSKU was last updated
     - Options: All time, Last 7/30/90 days, Custom range
     - Default: "All time" (shows all pending updates)
   - **Catalog Updated:** Filter items by when catalog was last updated
     - Options: Any time, Last 7/30/90 days, Never updated, Custom range
     - Default: "Any time"
   - **Max days pending:** Slider to limit how old updates can be
     - Set to 365 (default) to see all pending items
     - Lower values show only recent updates

5. **Click "Refresh Data"** to load the latest information

---

### Step 3: Review Pending Updates

**After clicking Refresh Data, you'll see:**

**Metrics at the top:**
- 📋 Total Updates Pending
- 🆕 New Items (items in BSKU but not in catalog)
- 🔄 Changed URLs (items where BSKU has a newer photo)
- 🏢 Number of merchants with updates

**Data table below:**
- Shows all pending updates
- Columns include:
  - Business ID
  - Merchant Supplied Item ID
  - Item Name
  - BSKU Photo URL (the new URL)
  - Current Catalog URL (the old URL)
  - Change Type (NEW_ITEM or URL_CHANGED)
  - When each was last updated
  - Who last updated the catalog

**Use the filters:**
- Filter by change type (NEW_ITEM vs URL_CHANGED)
- Filter by specific merchants
- Click on photo URLs to view the images

---

### Step 4: Download CSV for Bulk Upload

**When you're ready to update the catalog:**

1. **Review the pending updates** in the table
2. **Use the filters** if you only want to export certain items
3. **Scroll down to "Download CSV for Bulk Upload" section**

**You'll see:**
- How many files will be generated (based on 45,001 row limit)
- Total number of rows

**Click one of the download buttons:**

**Option A: Single CSV file** (if under 45,001 rows)
- Click "📥 Download CSV"
- File format: `photo_updates_YYYYMMDD_HHMMSS.csv`

**Option B: ZIP file** (if over 45,001 rows)
- Click "📦 Download ZIP"
- Contains multiple CSV files (part 1, part 2, etc.)
- Each file has max 45,001 rows
- File format: `photo_updates_YYYYMMDD_HHMMSS.zip`

**CSV Format:**
The downloaded files are ready for bulk upload:
```
businessId,itemMerchantSuppliedId,URL,angle,source
13055333,614557,https://images.wegmans.com/...,FRONT,MX
13055333,800043,https://images.wegmans.com/...,FRONT,MX
```

---

### Step 5: Create Photo IDs

1. **Go to your photo creation bulk tool** (ask your team where this is if unsure)

2. **Upload the CSV or ZIP file** you downloaded in Step 4
   - This tool will create photo IDs for each URL

3. **Wait for processing to complete**

4. **Download the output CSV files**
   - The output will include columns like:
     - `BUSINESS_ID`
     - `ITEM_MERCHANT_SUPPLIED_ID`
     - `PHOTO_ID` (this is what you need!)
     - Other columns (PHOTO_UUID, IMAGE_URL, etc.)

5. **Save these CSV files** - you'll upload them in the next step

---

### Step 6: Process Photo ID Output

**Back in the dashboard, scroll down to "Process Photo ID Output Files" section:**

1. **Click "Browse files"** under the file uploader

2. **Select all CSV files** you downloaded from the photo creation tool
   - You can select multiple files at once
   - Hold Ctrl (Windows) or Cmd (Mac) to select multiple

3. **Review the uploaded data:**
   - Dashboard shows how many files were uploaded
   - Expand each file to preview the data
   - See metrics: total rows, duplicates removed, merchant count

4. **Download catalog-ready files:**
   - Format: `businessId, itemMerchantSuppliedId, photoId`
   - Automatically splits into files ≤45,001 rows
   - Single CSV or ZIP with multiple files

---

### Step 7: Upload to Catalog

1. **Go to your catalog bulk tool** (ask your team where this is if unsure)

2. **Upload the catalog-ready CSV or ZIP** you just downloaded
   - This links the photo IDs to the catalog items

3. **Wait for processing to complete**

4. **Done!** Photo updates are now live in the catalog
   - Items won't reappear in the dashboard unless BSKU updates them again

---

### Step 8: Stop the Dashboard

**When you're finished:**

1. Go back to your terminal window
2. Press `Ctrl+C` to stop the dashboard
3. Close the browser tab

**To use it again:** Just run `streamlit run photo_update_dashboard.py` again!

---

## Understanding the Dashboard

### How Detection Works

The dashboard compares two sources:

**1. BSKU (Source of Truth)**
- Database: `BASELINE_SKU.PUBLIC.BASELINE_SKU_LATEST`
- Contains the authoritative photo URLs
- Has `updated_at` timestamp for each item

**2. Catalog (Current Published State)**
- Database: `x360.prod.merchant_catalog`
- Contains currently published photo URLs
- Has `mpc_updated_at` timestamp for each item

**Detection Logic:**
- **NEW_ITEM**: Item exists in BSKU but not in catalog → needs to be added
- **URL_CHANGED**: URLs are different AND BSKU was updated AFTER catalog → needs to be updated

**Smart filtering:**
- Only shows items where BSKU is newer than catalog
- Items automatically disappear from the list after you upload and catalog is updated
- Prevents showing items that don't actually need updating

---

## Troubleshooting

### Dashboard won't start

**Error: "Module not found"**
```bash
pip install -r requirements.txt
```
Or try: `pip3 install -r requirements.txt`

**Error: "streamlit: command not found"**
- Make sure you ran the pip install command above
- Try closing and reopening your terminal

---

### Connection to Snowflake fails

**Error: "Authentication failed" or "Connection error"**

1. **Check your secrets file:**
   ```bash
   cat .streamlit/secrets.toml
   ```

2. **Verify the format:**
   - `user` should be `FIRSTNAME.LASTNAME` (all caps, with period)
   - `password` should be your full PAT token (starts with `ghp_` or similar)
   - `account` should be `doordash` (lowercase, no extra text)
   - `warehouse` should be `ADHOC` (all caps)

3. **Generate a new PAT token:**
   - Old tokens expire
   - Go to PAT generator and create a fresh one
   - Update `.streamlit/secrets.toml` with new token

4. **Test your Snowflake access:**
   - Try logging into Snowflake Web UI: [https://doordash.snowflakecomputing.com](https://doordash.snowflakecomputing.com)
   - This confirms you have Snowflake access and verifies your username

---

### "No pending updates" shows up

**This is actually good!** It means:
- The catalog is up to date with BSKU
- All photo URLs are synced
- No action needed right now

**Want to verify it's working?**
- Try selecting different merchants
- Check back later (updates appear when BSKU changes)

---

### Dashboard shows old data

**Click the "🔄 Refresh Data" button** in the sidebar

**Or restart the dashboard:**
```bash
# Press Ctrl+C in terminal
# Then run again:
streamlit run photo_update_dashboard.py
```

---

### Can't find PAT generator

**Search in Slack:**
- "PAT generator"
- "Data Tools PAT"
- "Snowflake token"

**Ask your team:**
- "Where do I get a Snowflake PAT token?"
- Your manager or data lead should know

**Check internal docs:**
- Look for "Snowflake" or "Data Tools" documentation

---

### Don't know my warehouse name

**Most users: Use `ADHOC`**

**If that doesn't work:**
- Ask your manager which warehouse your team uses
- Common names: `COMPUTE_WH`, `ANALYTICS_WH`, team-specific warehouses

---

## Tips & Best Practices

### Daily Routine

**Morning check:**
1. Start dashboard: `streamlit run photo_update_dashboard.py`
2. Select your merchants
3. Click Refresh Data
4. Review pending updates

**If updates exist:**
1. Download CSV/ZIP
2. Upload to bulk tool
3. Items will disappear from dashboard after processing

**End of day:**
- Press Ctrl+C to stop the dashboard
- No need to keep it running when not in use

---

### Working with Multiple Merchants

**Efficient workflow:**
1. Select all merchants you manage in the dropdown
2. Use the merchant filter in the data table to focus on one at a time
3. Download once for all merchants (includes all in one file)
4. Or filter and download separately for each merchant

---

### Batch MSID Lookups

**When you have specific items to check:**
1. Get a list of MSIDs (Merchant Supplied Item IDs)
2. Paste them in "Search Specific MSIDs" box (one per line)
3. Click Refresh Data
4. Dashboard shows only those specific items

**Example use case:**
- Partner sends you a list of 50 items to check
- Paste the MSIDs instead of scrolling through thousands of rows

---

### Using Date Filters Effectively

**Common scenarios:**

**Daily updates (recommended):**
- BSKU Updated: "Last 7 days"
- Catalog Updated: "Any time"
- Max days pending: 365 (no limit)
- Shows: Recent BSKU changes that need updating

**Backlog cleanup:**
- BSKU Updated: "All time"
- Catalog Updated: "Any time"
- Max days pending: Adjust based on priority (e.g., 30 days for urgent items)
- Shows: All pending updates, oldest first

**Never-updated items:**
- BSKU Updated: "All time"
- Catalog Updated: "Never updated"
- Shows: Items in BSKU but never published to catalog

**Recent catalog updates:**
- BSKU Updated: "All time"
- Catalog Updated: "Last 7 days"
- Shows: Items where catalog was recently updated but BSKU is still newer

**Custom date ranges:**
- Use "Custom range" for both filters
- Select specific start and end dates
- Useful for investigating issues during a specific timeframe

---

### Download File Limits

**Why 45,001 rows?**
- Bulk upload tools have row limits
- Dashboard automatically splits large exports
- Each file stays under the limit

**If you get multiple files:**
- They're all in the ZIP
- Upload them one at a time, or all together (depending on your bulk tool)

---

## Getting Help

**Setup Issues:**
- Follow the troubleshooting section above
- Check your `.streamlit/secrets.toml` file carefully
- Verify your PAT token is fresh (not expired)

**Questions about the dashboard:**
- Contact Brian Schwartz
- Or your team's data lead

**Snowflake access issues:**
- Contact your data team or Snowflake admins
- Verify you have access to `PRODDB` database

**GitHub issues:**
- Report bugs or request features: [GitHub Issues](https://github.com/brian-schwartz-dd/photo-url-update-dashboard/issues)

---

## Quick Reference

### Commands

**Start dashboard:**
```bash
cd ~/Documents/photo-url-update-dashboard
streamlit run photo_update_dashboard.py
```

**Stop dashboard:**
```bash
Ctrl+C
```

**Update dashboard code:**
```bash
cd ~/Documents/photo-url-update-dashboard
git pull
```

**Reinstall dependencies:**
```bash
pip install -r requirements.txt
```

---

### File Locations

**Dashboard code:** `~/Documents/photo-url-update-dashboard/`

**Your secrets file:** `~/Documents/photo-url-update-dashboard/.streamlit/secrets.toml`

**Downloaded CSVs:** Usually in your `Downloads` folder

---

### Important Links

**GitHub Repository:** https://github.com/brian-schwartz-dd/photo-url-update-dashboard

**Snowflake Web UI:** https://doordash.snowflakecomputing.com

**Technical README:** See [README_DASHBOARD.md](README_DASHBOARD.md) in the repository

---

**Questions?** Contact Brian Schwartz or your data team lead.
