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

- **21 Pre-configured Merchants** - Quick selection dropdown
- **Auto-Detection** - Compares BSKU vs catalog timestamps
- **Batch MSID Search** - Look up specific items
- **CSV/ZIP Export** - Auto-splits files at 45k rows
- **Changelog Tracking** - See who/what updated each item

## Usage

1. Select merchants from the sidebar
2. Click "Refresh Data"
3. Review pending updates
4. Download CSV/ZIP for bulk upload
5. Upload to your bulk tool

## Full Documentation

See [README_DASHBOARD.md](README_DASHBOARD.md) for complete setup instructions, troubleshooting, and technical details.

## Requirements

- Python 3.8+
- Snowflake access (PRODDB)
- PAT token from Data Tools

## Documentation

- **[User Guide](USER_GUIDE.md)** - Complete walkthrough for first-time users
- **[Technical README](README_DASHBOARD.md)** - Detailed setup, configuration, and troubleshooting
- **[GitHub Repository](https://github.com/brian-schwartz-dd/photo-url-update-dashboard)** - Code and issues

## Support

Questions? Contact Brian Schwartz or your data team.
