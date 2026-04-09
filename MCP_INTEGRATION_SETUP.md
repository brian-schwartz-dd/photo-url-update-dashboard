# MCP Integration Setup for Photo Update Dashboard

The Photo Update Dashboard now integrates with DoorDash's Bulk Tools MCP to provide a fully automated workflow:

**Query → Generate CSV → Validate → Open Bulk Tools (with file pre-loaded)**

## Prerequisites

1. **Bulk Tools MCP Server installed**
2. **Dashboard running** (`streamlit run photo_update_dashboard.py`)
3. **Bulk Tools access** via Okta SSO

---

## Installation

### Step 1: Install Bulk Tools MCP

Run these commands in your terminal:

```bash
git clone https://github.com/doordash/nv-operator-tooling-poc.git /tmp/nv-operator-tooling-poc
bash /tmp/nv-operator-tooling-poc/bulk-tools-mcp/scripts/install.sh
```

This will:
- Install the MCP server at `~/.bulk-tools-mcp/`
- Set up authentication
- Configure Cursor (optional, not needed for dashboard)

### Step 2: Authenticate with Bulk Tools

The first time you use the integration, you'll need to log in:

1. Open Cursor or Claude Code
2. Ask: "Log me in to bulk tools"
3. A browser will open for Okta SSO login
4. Complete the login flow

**Note:** Authentication is shared across all MCP clients, so once you log in via Cursor, the dashboard will work automatically.

### Step 3: Verify Installation

Run this in your terminal to check if MCP is installed:

```bash
ls ~/.bulk-tools-mcp/venv/bin/bulk-tools-mcp
```

You should see the path printed. If not, repeat Step 1.

---

## How to Use

### Workflow

1. **Open Dashboard**
   ```bash
   cd ~/photo-url-update-dashboard
   streamlit run photo_update_dashboard.py
   ```

2. **Select Use Case**
   - Use Case A: Baseline URL Query (BSKU vs Catalog)
   - Use Case B: Red Build Item Name Match Query

3. **Run Query**
   - For Use Case A: Select merchants, dates, run query
   - For Use Case B: Click "Run Red Build Query"

4. **Review Results**
   - Check the data preview
   - Verify row counts

5. **Click "🚀 Open in Bulk Tools"**
   - Dashboard validates the CSV against Bulk Tools schema
   - Automatically saves CSV to `/tmp/photo_updates/`
   - Opens Bulk Tools UI in your browser
   - **CSV is already loaded** in the browser window

6. **Complete Upload in Browser**
   - Review the pre-loaded file
   - Click "Submit" in Bulk Tools UI
   - Monitor job status

---

## Understanding the Integration

### What Happens When You Click "Open in Bulk Tools"

```
┌─────────────────────────────────────────────────────────┐
│ 1. Dashboard saves CSV to /tmp/photo_updates/          │
│    └─> photo_updates_YYYYMMDD_HHMMSS.csv               │
├─────────────────────────────────────────────────────────┤
│ 2. Calls MCP Server to validate CSV                    │
│    └─> bulk_prepare_csv(operation, csv_path)           │
│    └─> Checks column names, data types, format         │
├─────────────────────────────────────────────────────────┤
│ 3. If validation passes, calls MCP to open browser     │
│    └─> bulk_open_in_browser(operation, csv_path)       │
│    └─> Opens Bulk Tools UI with file pre-loaded        │
├─────────────────────────────────────────────────────────┤
│ 4. Browser window opens with your CSV ready to submit  │
│    └─> You just click "Submit" to complete the upload  │
└─────────────────────────────────────────────────────────┘
```

### MCP Tools Used

The dashboard uses these MCP tools from `mcp_integration.py`:

- **`bulk_list_operations`**: Finds available bulk operations
- **`bulk_prepare_csv`**: Validates CSV format against schema
- **`bulk_open_in_browser`**: Opens Bulk Tools with file loaded

### CSV Validation

The MCP server validates:
- ✅ Column names match schema (`businessId`, `itemMerchantSuppliedId`, `URL`, `angle`, `source`)
- ✅ Required columns are present
- ✅ Data types are correct
- ✅ Row format matches bulk tool requirements

If validation fails, you'll see an error with details about what needs to be fixed.

---

## Configuration

### Bulk Operation Names

The dashboard uses these operation names by default:

```python
BULK_OPERATION_FETCH_PHOTO = "fetch_photo_metadata"  # Create Photo ID/URL
BULK_OPERATION_UPDATE_CATALOG = "update_product_item"  # Update Merchant Catalog
```

The main queries (Use Case A and B) use `update_product_item` to update the merchant catalog with photo URLs.

**If you need to change the operation names:**

1. Update lines ~19-20 in `photo_update_dashboard.py`:
   ```python
   BULK_OPERATION_FETCH_PHOTO = "fetch_photo_metadata"
   BULK_OPERATION_UPDATE_CATALOG = "update_product_item"
   ```

### Temporary File Location

CSVs are saved to `/tmp/photo_updates/` by default. To change this:

```python
# In photo_update_dashboard.py, find:
temp_dir = Path(tempfile.gettempdir()) / "photo_updates"

# Change to your preferred location:
temp_dir = Path("/your/custom/path")
```

---

## Troubleshooting

### "MCP integration not available"

**Cause:** `mcp_integration.py` not found or import failed

**Fix:**
1. Verify both files are in the same directory:
   ```bash
   ls ~/photo-url-update-dashboard/photo_update_dashboard.py
   ls ~/photo-url-update-dashboard/mcp_integration.py
   ```
2. Restart the dashboard

### "MCP Server not found"

**Cause:** Bulk Tools MCP not installed

**Fix:**
```bash
bash ~/.bulk-tools-mcp/src/bulk-tools-mcp/scripts/install.sh
```

### "CSV validation failed"

**Cause:** CSV format doesn't match bulk tool schema

**Fix:**
- Check the error message for specific column issues
- Verify your CSV has: `businessId`, `itemMerchantSuppliedId`, `URL`, `angle`, `source`
- Re-run the query to regenerate the CSV

### "Authentication token expired"

**Cause:** Okta SSO token needs refresh

**Fix:**
1. Open Cursor
2. Ask: "Log me in to bulk tools"
3. Complete the login flow
4. Try the dashboard again

### Browser doesn't open

**Cause:** MCP `bulk_open_in_browser` tool failed

**Workaround:**
1. Check the error message
2. Download CSV manually using the download button
3. Open Bulk Tools manually and upload

---

## Manual Workflow (if MCP not available)

If you can't install MCP or it's not working:

1. **Run query** in dashboard
2. **Download CSV** using the download button
3. **Open Bulk Tools** manually in your browser
4. **Upload CSV** through the standard UI
5. **Submit job**

The MCP integration just automates steps 3-4.

---

## Advanced: Finding the Correct Operation

If you need to verify or find different bulk operations:

1. Open Cursor or Claude Code
2. Run these commands:

```
List all bulk operation categories

List operations in the "retail_catalog" category

Show me the schema for "update_product_item"
```

3. The `update_product_item` operation should match these columns:
   - `businessId`
   - `itemMerchantSuppliedId`
   - `URL`
   - `angle`
   - `source`

4. If needed, update `BULK_OPERATION_UPDATE_CATALOG` in the dashboard code

---

## Support

- **MCP Issues**: Contact John Plocharczyk or Prashant Verma
- **Dashboard Issues**: Check [photo-url-update-dashboard GitHub](https://github.com/brian-schwartz-dd/photo-url-update-dashboard)
- **Bulk Tools Issues**: See internal Bulk Tools documentation

---

## Benefits of MCP Integration

✅ **One-Click Workflow**: Query → Validate → Open Bulk Tools
✅ **Automatic Validation**: Catches CSV format errors before upload
✅ **File Pre-Loading**: No manual file selection in browser
✅ **Error Prevention**: Schema validation prevents rejected jobs
✅ **Time Savings**: ~3-4 steps eliminated from manual workflow

---

## Files

- **`mcp_integration.py`**: MCP client library
- **`photo_update_dashboard.py`**: Main dashboard with MCP integration
- **`MCP_INTEGRATION_SETUP.md`**: This file

---

## Version History

- **v2.1**: Added MCP integration for automated Bulk Tools opening
- **v2.0**: Added Use Case B (Red Build query)
- **v1.0**: Initial dashboard with Use Case A (BSKU vs Catalog)
