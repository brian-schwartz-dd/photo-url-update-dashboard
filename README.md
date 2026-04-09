# Photo URL Update Dashboard

Streamlit dashboard for managing photo URL updates from BSKU to catalog.

![Dashboard Preview](https://img.shields.io/badge/streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/python-3.8+-blue?style=for-the-badge&logo=python&logoColor=white)

## What This Does

Automatically detects photo URL updates that need to be synced from BSKU to the merchant catalog, and exports them in a format ready for bulk upload.

**📖 New to this tool? Start here:** [Complete User Guide](USER_GUIDE.md) - Step-by-step instructions from setup to daily use.

## Quick Start

### 1. Clone and Install

```bash
git clone https://github.com/brian-schwartz-dd/photo-url-update-dashboard.git
cd photo-url-update-dashboard
pip install -r requirements.txt
```

### 2. Configure Snowflake

Create `.streamlit/secrets.toml`:

```toml
[snowflake]
user = "FIRSTNAME.LASTNAME"
password = "your_PAT_token_here"
account = "doordash"
warehouse = "ADHOC"
database = "PRODDB"
schema = "static"
```

**Get your PAT token:** Ask your team for the Data Tools PAT Generator link.

### 3. Run

```bash
streamlit run photo_update_dashboard.py
```

Opens at `http://localhost:8501`

---

## Features

### Core Features
- **21 Pre-configured Merchants** - Quick selection dropdown
- **Auto-Detection** - Compares BSKU vs catalog timestamps
- **Advanced Date Filtering** - Filter by BSKU update date, catalog update date, or days pending
- **Batch MSID Search** - Look up specific items
- **CSV/ZIP Export** - Auto-splits files at 45k rows
- **Photo ID Processing** - Upload photo creation output and generate catalog-ready files
- **Changelog Tracking** - See who/what updated each item

### New Features (v2.1)
- **🚀 MCP Integration** - Automated Bulk Tools workflow: Query → Validate → Auto-open browser with CSV pre-loaded ([Setup Guide](MCP_INTEGRATION_SETUP.md))
- **Dual Use Cases**:
  - **Use Case A**: Baseline URL Query (BSKU vs Catalog) - Two-step workflow with photo ID creation
  - **Use Case B**: Red Build Item Name Match Query - Direct catalog update with vendor-matched photos
- **Auto Token Refresh** - Seamless Snowflake reconnection on token expiration
- **MSID Protection** - Leading underscore preserves zeros in Excel (e.g., `_00123`)

## Usage

### Use Case A: Baseline URL Query (BSKU vs Catalog)
**Two-step workflow:**
1. Select merchants and filters → Run query
2. Click **"🚀 Open in Bulk Tools"** → Creates photo IDs from URLs
3. Download photo ID output from Bulk Tools
4. Upload to "Process Photo ID Output Files" section
5. Click **"🚀 Open in Bulk Tools"** → Updates catalog with photo IDs

### Use Case B: Red Build Item Name Match Query
**One-step workflow (vendor photos already have photo IDs):**
1. Click **"🚀 Run Red Build Query"**
2. Click **"🚀 Open in Bulk Tools"** → Updates catalog directly

### MCP Integration (Optional but Recommended)
- **Automated**: Browser opens with CSV pre-loaded, just click "Submit"
- **Manual**: Download CSV and upload to Bulk Tools manually
- **Setup**: See [MCP_INTEGRATION_SETUP.md](MCP_INTEGRATION_SETUP.md)

**See [User Guide](USER_GUIDE.md) for detailed step-by-step instructions.**

## Full Documentation

See [README_DASHBOARD.md](README_DASHBOARD.md) for complete setup instructions, troubleshooting, and technical details.

## Requirements

- Python 3.8+
- Snowflake access (PRODDB)
- PAT token from Data Tools

## Documentation

- **[User Guide](USER_GUIDE.md)** - Complete walkthrough for first-time users
- **[MCP Integration Setup](MCP_INTEGRATION_SETUP.md)** - Automated Bulk Tools workflow setup
- **[Technical README](README_DASHBOARD.md)** - Detailed setup, configuration, and troubleshooting
- **[Image Validation Tool](IMAGE_VALIDATION_README.md)** - GPT-4 Vision image-item name validation
- **[GitHub Repository](https://github.com/brian-schwartz-dd/photo-url-update-dashboard)** - Code and issues

## Support

Questions? Contact Brian Schwartz or your data team.
