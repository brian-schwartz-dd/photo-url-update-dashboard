import streamlit as st
import snowflake.connector
import pandas as pd
from datetime import datetime
import io
import zipfile

# ============================================
# PAGE CONFIG
# ============================================
st.set_page_config(
    page_title="Photo URL Update Dashboard",
    page_icon="📸",
    layout="wide"
)

st.title("📸 Photo URL Update Dashboard")
st.markdown("---")

# ============================================
# SNOWFLAKE CONNECTION
# ============================================
@st.cache_resource
def get_snowflake_connection():
    """Create Snowflake connection"""
    conn_params = {
        "user": st.secrets["snowflake"]["user"],
        "password": st.secrets["snowflake"]["password"],
        "account": st.secrets["snowflake"]["account"],
        "warehouse": st.secrets["snowflake"]["warehouse"],
        "database": st.secrets["snowflake"]["database"],
        "schema": st.secrets["snowflake"]["schema"]
    }

    # Add role if specified (optional)
    if "role" in st.secrets["snowflake"]:
        conn_params["role"] = st.secrets["snowflake"]["role"]

    return snowflake.connector.connect(**conn_params)

def execute_query(query, params=None):
    """Execute a query and return results as DataFrame"""
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        columns = [col[0] for col in cursor.description] if cursor.description else []
        results = cursor.fetchall()
        return pd.DataFrame(results, columns=columns)
    finally:
        cursor.close()

# ============================================
# MERCHANT CONFIGURATION
# ============================================
st.sidebar.header("🏢 Merchant Selection")

# Get available merchants
AVAILABLE_MERCHANTS = {
    "11253649": "Wild Fork",
    "13625077": "Schnucks",
    "1048127": "New Seasons",
    "13104513": "Milam's",
    "11129311": "Raley's",
    "11125334": "Nob Hill",
    "11125332": "Bel Air",
    "11125340": "AJ's Fine Foods",
    "11129263": "Food City",
    "11237357": "Bashas (Grocery)",
    "11184482": "Eddie's Country Store",
    "928488": "Bristol Farms",
    "1048116": "New Leaf",
    "932532": "Lazy Acres",
    "16280079": "Harmons",
    "11143864": "Dierbergs",
    "11396919": "Aldi",
    "13055333": "Wegmans",
    "17288245": "Farm Boy",
    "14049297": "Costco",
    "434736": "Meijer",
}

selected_merchants = st.sidebar.multiselect(
    "Select Business IDs:",
    options=list(AVAILABLE_MERCHANTS.keys()),
    default=[],
    format_func=lambda x: f"{x} - {AVAILABLE_MERCHANTS[x]}"
)

# Allow custom business IDs
st.sidebar.markdown("---")
st.sidebar.subheader("➕ Add Custom Business IDs")
custom_ids = st.sidebar.text_area(
    "Enter additional Business IDs (one per line):",
    help="Add business IDs that aren't in the dropdown above"
)

# Parse custom IDs and add to selected list
if custom_ids:
    custom_id_list = [id.strip() for id in custom_ids.split('\n') if id.strip()]
    selected_merchants = list(set(selected_merchants + custom_id_list))

if not selected_merchants:
    st.warning("⚠️ Please select at least one merchant to continue.")
    st.stop()

# Allow specific MSID search
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Search Specific MSIDs (Optional)")
specific_msids = st.sidebar.text_area(
    "Enter Merchant Supplied Item IDs (one per line):",
    help="Leave empty to see all items, or enter specific MSIDs to search for"
)

# Parse MSIDs
msid_filter_list = []
if specific_msids:
    msid_filter_list = [msid.strip() for msid in specific_msids.split('\n') if msid.strip()]

# ============================================
# QUERY PENDING UPDATES
# ============================================
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_pending_updates(merchant_list, msid_filter=None):
    """Get pending photo updates for selected merchants"""
    merchant_ids = "', '".join(merchant_list)

    # Build MSID filter if provided
    msid_filter_clause = ""
    if msid_filter and len(msid_filter) > 0:
        msid_list = "', '".join(msid_filter)
        msid_filter_clause = f"AND merchant_supplied_item_id IN ('{msid_list}')"

    query = f"""
    WITH bsku_current AS (
      SELECT
        business_id,
        merchant_supplied_item_id,
        CONCAT(business_id, '_', merchant_supplied_item_id) AS business_msid,
        bsku_photo_url,
        created_at,
        updated_at
      FROM (
        SELECT
          business_id,
          merchant_supplied_item_id,
          JSON_EXTRACT_PATH_TEXT(attributes, 'product.imageUrl') AS bsku_photo_url,
          created_at,
          updated_at,
          ROW_NUMBER() OVER (
            PARTITION BY business_id, merchant_supplied_item_id
            ORDER BY updated_at DESC, created_at DESC
          ) AS rn
        FROM BASELINE_SKU.PUBLIC.BASELINE_SKU_LATEST
        WHERE business_id IN ('{merchant_ids}')
          AND JSON_EXTRACT_PATH_TEXT(attributes, 'product.imageUrl') IS NOT NULL
          AND TRIM(JSON_EXTRACT_PATH_TEXT(attributes, 'product.imageUrl')) != ''
          AND JSON_EXTRACT_PATH_TEXT(attributes, 'product.imageUrl') != 'default_image_url'
          {msid_filter_clause}
      )
      WHERE rn = 1
    ),

    catalog_current AS (
      SELECT
        CONCAT(business_id, '_', item_merchant_supplied_id) AS business_msid,
        photo_url AS catalog_photo_url,
        mpc_updated_at AS catalog_updated_at,
        mpc_updated_by AS catalog_updated_by,
        item_name
      FROM x360.prod.merchant_catalog
      WHERE business_id IN ('{merchant_ids}')
    )

    SELECT
      b.business_id,
      b.merchant_supplied_item_id,
      b.business_msid,
      c.item_name,
      b.bsku_photo_url AS new_photo_url,
      c.catalog_photo_url AS current_catalog_url,
      b.updated_at AS bsku_updated_at,
      c.catalog_updated_at,
      CASE
        WHEN c.catalog_updated_by = '0' AND c.catalog_updated_at < TIMESTAMP '2024-02-01 00:00:00' THEN 'Detect & Fix or Unspecified User'
        WHEN c.catalog_updated_by = '0' AND c.catalog_updated_at >= TIMESTAMP '2024-02-01 00:00:00' THEN 'Unspecified User'
        WHEN c.catalog_updated_by = '-1' THEN 'Catalog Builder'
        WHEN c.catalog_updated_by = '-2' THEN 'Detect & Fix'
        WHEN c.catalog_updated_by = '-3' THEN 'URPC From 3P'
        WHEN c.catalog_updated_by = '-4' THEN 'Green Pipeline'
        WHEN c.catalog_updated_by = '-5' THEN 'Optimus Pipeline'
        WHEN c.catalog_updated_by = '-6' THEN 'Kaizen Platform'
        WHEN c.catalog_updated_by = '-7' THEN 'Dashmart Service'
        WHEN c.catalog_updated_by = '-8' THEN 'Pulse Test'
        WHEN c.catalog_updated_by = '-9' THEN 'Observable Config'
        WHEN c.catalog_updated_by = '-10' THEN 'Linking'
        ELSE CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, ''))
      END AS catalog_updated_by_name,
      DATEDIFF('day', b.updated_at, CURRENT_TIMESTAMP) AS days_since_bsku_update,
      CASE
        WHEN c.business_msid IS NULL THEN 'NEW_ITEM'
        WHEN COALESCE(TRIM(b.bsku_photo_url), '') != COALESCE(TRIM(c.catalog_photo_url), '')
             AND b.updated_at > COALESCE(c.catalog_updated_at, '1900-01-01') THEN 'URL_CHANGED'
        ELSE 'NO_CHANGE'
      END AS change_type
    FROM bsku_current b
    LEFT JOIN catalog_current c
      ON b.business_msid = c.business_msid
    LEFT JOIN proddb.public.dimension_users u
      ON c.catalog_updated_by = u.user_id
    WHERE change_type IN ('NEW_ITEM', 'URL_CHANGED')
    ORDER BY b.updated_at DESC, b.business_msid
    """

    return execute_query(query)

# Load data
with st.spinner("🔍 Querying pending photo updates..."):
    df = get_pending_updates(selected_merchants, msid_filter_list)

# ============================================
# METRICS DISPLAY
# ============================================
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📋 Total Updates Pending", len(df))

with col2:
    new_items = len(df[df['CHANGE_TYPE'] == 'NEW_ITEM']) if len(df) > 0 else 0
    st.metric("🆕 New Items", new_items)

with col3:
    changed_urls = len(df[df['CHANGE_TYPE'] == 'URL_CHANGED']) if len(df) > 0 else 0
    st.metric("🔄 Changed URLs", changed_urls)

with col4:
    merchants_count = len(df['BUSINESS_ID'].unique()) if len(df) > 0 else 0
    st.metric("🏢 Merchants", merchants_count)

st.markdown("---")

# Show MSID filter info if active
if msid_filter_list:
    st.info(f"🔍 Filtering by {len(msid_filter_list)} specific MSID(s)")

# ============================================
# DATA DISPLAY
# ============================================
if len(df) > 0:
    st.subheader("📊 Pending Updates")

    # Add filters
    col_filter1, col_filter2 = st.columns(2)

    with col_filter1:
        filter_change_type = st.multiselect(
            "Filter by Change Type:",
            options=['NEW_ITEM', 'URL_CHANGED'],
            default=['NEW_ITEM', 'URL_CHANGED']
        )

    with col_filter2:
        filter_merchants = st.multiselect(
            "Filter by Merchant:",
            options=df['BUSINESS_ID'].unique().tolist(),
            default=df['BUSINESS_ID'].unique().tolist()
        )

    # Apply filters
    filtered_df = df[
        (df['CHANGE_TYPE'].isin(filter_change_type)) &
        (df['BUSINESS_ID'].isin(filter_merchants))
    ]

    st.info(f"📋 Showing {len(filtered_df):,} of {len(df):,} total updates")

    # Display data
    st.dataframe(
        filtered_df[[
            'BUSINESS_ID', 'MERCHANT_SUPPLIED_ITEM_ID', 'ITEM_NAME',
            'NEW_PHOTO_URL', 'CURRENT_CATALOG_URL', 'CHANGE_TYPE',
            'BSKU_UPDATED_AT', 'CATALOG_UPDATED_AT', 'CATALOG_UPDATED_BY_NAME'
        ]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "ITEM_NAME": "Item Name",
            "NEW_PHOTO_URL": st.column_config.LinkColumn("BSKU Photo URL"),
            "CURRENT_CATALOG_URL": st.column_config.LinkColumn("Catalog Photo URL"),
            "BSKU_UPDATED_AT": "BSKU Updated",
            "CATALOG_UPDATED_AT": "Catalog Updated",
            "CATALOG_UPDATED_BY_NAME": "Updated By"
        }
    )

    st.markdown("---")

    # ============================================
    # DOWNLOAD FUNCTIONALITY
    # ============================================
    st.subheader("⬇️ Download CSV for Bulk Upload")

    MAX_ROWS_PER_FILE = 45001

    # Prepare download data in correct format
    download_df = filtered_df[['BUSINESS_ID', 'MERCHANT_SUPPLIED_ITEM_ID', 'NEW_PHOTO_URL']].copy()
    download_df.columns = ['businessId', 'itemMerchantSuppliedId', 'URL']

    # Add required constant fields
    download_df['angle'] = 'FRONT'
    download_df['source'] = 'MX'

    # Reorder columns to match expected format
    download_df = download_df[['businessId', 'itemMerchantSuppliedId', 'URL', 'angle', 'source']]

    total_rows = len(download_df)
    num_files = (total_rows // MAX_ROWS_PER_FILE) + (1 if total_rows % MAX_ROWS_PER_FILE > 0 else 0)

    st.info(f"📦 Will generate {num_files} file(s) for {total_rows:,} rows (max {MAX_ROWS_PER_FILE:,} rows per file)")

    col_download1, col_download2 = st.columns(2)

    with col_download1:
        if num_files == 1:
            # Single file download
            csv_buffer = io.StringIO()
            download_df.to_csv(csv_buffer, index=False)
            csv_data = csv_buffer.getvalue()

            st.download_button(
                label=f"📥 Download CSV ({total_rows:,} rows)",
                data=csv_data,
                file_name=f"photo_updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )
        else:
            # Multiple files - create ZIP
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i in range(num_files):
                    start_idx = i * MAX_ROWS_PER_FILE
                    end_idx = min((i + 1) * MAX_ROWS_PER_FILE, total_rows)

                    chunk_df = download_df.iloc[start_idx:end_idx]

                    csv_buffer = io.StringIO()
                    chunk_df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    filename = f"photo_updates_part{i+1}_of_{num_files}.csv"
                    zip_file.writestr(filename, csv_data)

            zip_data = zip_buffer.getvalue()

            st.download_button(
                label=f"📦 Download ZIP ({num_files} files, {total_rows:,} rows)",
                data=zip_data,
                file_name=f"photo_updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                type="primary",
                use_container_width=True
            )

    with col_download2:
        # Preview download format
        with st.expander("👁️ Preview Download Format"):
            st.dataframe(download_df.head(10), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.info("""
    💡 **How it works:**
    - Dashboard compares BSKU photo URLs with catalog URLs
    - Shows items where BSKU was updated AFTER catalog (catalog needs updating)
    - Download CSV with format: businessId, itemMerchantSuppliedId, URL, angle, source
    - Upload to bulk tool (angle=FRONT, source=MX added automatically)
    - Once uploaded, items won't reappear unless BSKU updates again
    """)

else:
    st.success("🎉 No pending photo updates! All items are up to date.")
    st.info("💡 New updates will appear here when BSKU data changes.")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Dashboard v2.0")
