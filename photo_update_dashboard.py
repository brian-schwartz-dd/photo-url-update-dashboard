import streamlit as st
import snowflake.connector
import pandas as pd
from datetime import datetime
import io
import zipfile
import tempfile
from pathlib import Path

# Import MCP integration
try:
    from mcp_integration import MCPClient, validate_and_open, find_photo_operation
    MCP_AVAILABLE = True
    MCP_ERROR = None
except ImportError as e:
    MCP_AVAILABLE = False
    MCP_ERROR = f"Import error: {str(e)}"
except Exception as e:
    MCP_AVAILABLE = False
    MCP_ERROR = f"Unexpected error: {str(e)}"

# ============================================
# CONSTANTS
# ============================================
MAX_ROWS_PER_FILE = 45001  # Max rows per CSV file for bulk upload

# Bulk Tools MCP operations
BULK_CATEGORY_RETAIL_CATALOG = "retail_catalog"
BULK_OPERATION_FETCH_PHOTO = "fetch_photo_metadata"  # Create Photo ID/URL
BULK_OPERATION_UPDATE_CATALOG = "update_product_item"  # Update Merchant Catalog

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
# PHOTO ID UPLOAD & PROCESSING
# ============================================
st.header("📤 Process Photo ID Output Files")
st.markdown("""
Upload the CSV files you received after creating photo IDs in the bulk tool.
This will generate catalog-ready files with format: `businessId, itemMerchantSuppliedId, photoId`
""")

uploaded_files = st.file_uploader(
    "Upload Photo ID CSV files (multiple files allowed):",
    type=['csv'],
    accept_multiple_files=True,
    help="Select all CSV files containing photo IDs from the bulk tool output",
    key="photo_id_uploader"
)

if uploaded_files:
    st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

    # Process all uploaded files
    all_photo_ids = []

    for uploaded_file in uploaded_files:
        try:
            df_upload = pd.read_csv(uploaded_file)

            # Display file info
            with st.expander(f"📄 {uploaded_file.name} ({len(df_upload):,} rows)"):
                st.dataframe(df_upload.head(10), use_container_width=True, hide_index=True)

            # Extract the three required columns
            # Try to find columns with flexible naming
            business_id_col = None
            msid_col = None
            photo_id_col = None

            for col in df_upload.columns:
                col_lower = col.lower().replace('_', '').replace(' ', '')
                if 'businessid' in col_lower:
                    business_id_col = col
                elif 'itemmerchant' in col_lower or 'msid' in col_lower:
                    msid_col = col
                elif 'photoid' in col_lower:
                    photo_id_col = col

            if not all([business_id_col, msid_col, photo_id_col]):
                st.error(f"❌ {uploaded_file.name}: Could not find required columns (businessId, itemMerchantSuppliedId, photoId)")
                continue

            # Extract and standardize
            df_extract = df_upload[[business_id_col, msid_col, photo_id_col]].copy()
            df_extract.columns = ['businessId', 'itemMerchantSuppliedId', 'photoId']

            # Add leading underscore to MSID to preserve leading zeros in Excel
            df_extract['itemMerchantSuppliedId'] = '_' + df_extract['itemMerchantSuppliedId'].astype(str)

            # Remove any rows with missing values
            df_extract = df_extract.dropna()

            all_photo_ids.append(df_extract)

        except Exception as e:
            st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")

    if all_photo_ids:
        # Combine all uploaded files
        combined_df = pd.concat(all_photo_ids, ignore_index=True)

        # Remove duplicates (keep first occurrence)
        original_count = len(combined_df)
        combined_df = combined_df.drop_duplicates(subset=['businessId', 'itemMerchantSuppliedId'], keep='first')
        duplicates_removed = original_count - len(combined_df)

        st.markdown("---")
        st.subheader("📊 Combined Photo ID Data")

        col_info1, col_info2, col_info3 = st.columns(3)
        with col_info1:
            st.metric("Total Rows", f"{len(combined_df):,}")
        with col_info2:
            st.metric("Duplicates Removed", f"{duplicates_removed:,}")
        with col_info3:
            st.metric("Merchants", len(combined_df['businessId'].unique()))

        # Preview combined data
        with st.expander("👁️ Preview Combined Data"):
            st.dataframe(combined_df.head(20), use_container_width=True, hide_index=True)

        # Download section
        st.markdown("---")
        st.subheader("⬇️ Download Catalog-Ready Files")

        total_rows = len(combined_df)
        num_files = (total_rows // MAX_ROWS_PER_FILE) + (1 if total_rows % MAX_ROWS_PER_FILE > 0 else 0)

        st.info(f"📦 Will generate {num_files} file(s) for {total_rows:,} rows (max {MAX_ROWS_PER_FILE:,} rows per file)")

        col_dl1, col_dl2 = st.columns(2)

        with col_dl1:
            if num_files == 1:
                # Single file download
                csv_buffer = io.StringIO()
                combined_df.to_csv(csv_buffer, index=False)
                csv_data = csv_buffer.getvalue()

                st.download_button(
                    label=f"📥 Download CSV ({total_rows:,} rows)",
                    data=csv_data,
                    file_name=f"photo_ids_catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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

                        chunk_df = combined_df.iloc[start_idx:end_idx]

                        csv_buffer = io.StringIO()
                        chunk_df.to_csv(csv_buffer, index=False)
                        csv_data = csv_buffer.getvalue()

                        filename = f"photo_ids_catalog_part{i+1}_of_{num_files}.csv"
                        zip_file.writestr(filename, csv_data)

                zip_data = zip_buffer.getvalue()

                st.download_button(
                    label=f"📦 Download ZIP ({num_files} files, {total_rows:,} rows)",
                    data=zip_data,
                    file_name=f"photo_ids_catalog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )

        with col_dl2:
            st.info("""
            **Next steps:**
            1. Download the CSV/ZIP file
            2. Upload to catalog bulk tool
            3. Photo IDs will be linked to items
            """)

        st.markdown("---")
        st.success("✅ Files are ready! Upload to catalog bulk tool to complete the photo update process.")

else:
    st.info("👆 Upload photo ID CSV files above to process them for catalog upload")

st.markdown("---")
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
    try:
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
    except snowflake.connector.errors.ProgrammingError as e:
        # Check if it's an authentication token expiration error
        if '390114' in str(e) or 'Authentication token has expired' in str(e):
            # Clear the cached connection and retry
            st.cache_resource.clear()
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
        else:
            # Re-raise other errors
            raise

# ============================================
# USE CASE SELECTION
# ============================================
st.header("🔍 Photo URL Query Tool")
st.markdown("Select the type of query you want to run:")

use_case = st.selectbox(
    "Select Use Case:",
    options=["Use Case A: Baseline URL Query", "Use Case B: Red Build Item Name Match Query"],
    help="Choose which query to run based on your workflow"
)

st.markdown("---")

# ============================================
# USE CASE A: BASELINE URL QUERY
# ============================================
if use_case == "Use Case A: Baseline URL Query":
    st.subheader("📊 Baseline URL Query: BSKU vs Catalog")
    st.markdown("Compare BSKU photo URLs with catalog to find items needing updates.")

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

    # Date/Time Filtering
    st.sidebar.markdown("---")
    st.sidebar.subheader("📅 Date Filters")

    # BSKU Update Date Filter
    bsku_date_filter = st.sidebar.selectbox(
        "BSKU Updated:",
        options=["All time", "Last 7 days", "Last 30 days", "Last 90 days", "Custom range"],
        help="Filter items by when BSKU was last updated"
    )

    bsku_start_date = None
    bsku_end_date = None
    if bsku_date_filter == "Custom range":
        col_date1, col_date2 = st.sidebar.columns(2)
        with col_date1:
            bsku_start_date = st.date_input("From:", value=None)
        with col_date2:
            bsku_end_date = st.date_input("To:", value=None)

    # Catalog Update Date Filter
    catalog_date_filter = st.sidebar.selectbox(
        "Catalog Updated:",
        options=["Any time", "Last 7 days", "Last 30 days", "Last 90 days", "Never updated", "Custom range"],
        help="Filter items by when catalog was last updated"
    )

    catalog_start_date = None
    catalog_end_date = None
    if catalog_date_filter == "Custom range":
        col_date3, col_date4 = st.sidebar.columns(2)
        with col_date3:
            catalog_start_date = st.date_input("Cat From:", value=None, key="cat_from")
        with col_date4:
            catalog_end_date = st.date_input("Cat To:", value=None, key="cat_to")

    # Days Pending Filter
    days_pending_filter = st.sidebar.slider(
        "Max days pending:",
        min_value=0,
        max_value=365,
        value=365,
        step=1,
        help="Only show items pending for up to this many days (0 = no limit)"
    )
    if days_pending_filter == 0:
        days_pending_filter = None

    # ============================================
    # QUERY PENDING UPDATES
    # ============================================
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh Data", type="primary"):
        st.cache_data.clear()
        st.rerun()

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_pending_updates(merchant_list, msid_filter=None, bsku_date_filter=None, bsku_start=None, bsku_end=None,
                           catalog_date_filter=None, catalog_start=None, catalog_end=None, max_days_pending=None):
        """Get pending photo updates for selected merchants"""
        merchant_ids = "', '".join(merchant_list)

        # Build MSID filter if provided
        msid_filter_clause = ""
        if msid_filter and len(msid_filter) > 0:
            msid_list = "', '".join(msid_filter)
            msid_filter_clause = f"AND merchant_supplied_item_id IN ('{msid_list}')"

        # Build BSKU date filter
        bsku_date_clause = ""
        if bsku_date_filter == "Last 7 days":
            bsku_date_clause = "AND updated_at >= DATEADD('day', -7, CURRENT_TIMESTAMP)"
        elif bsku_date_filter == "Last 30 days":
            bsku_date_clause = "AND updated_at >= DATEADD('day', -30, CURRENT_TIMESTAMP)"
        elif bsku_date_filter == "Last 90 days":
            bsku_date_clause = "AND updated_at >= DATEADD('day', -90, CURRENT_TIMESTAMP)"
        elif bsku_date_filter == "Custom range" and bsku_start and bsku_end:
            bsku_date_clause = f"AND updated_at BETWEEN '{bsku_start}' AND '{bsku_end}'"

        # Build catalog date filter (applied in final WHERE clause)
        catalog_date_clause = ""
        if catalog_date_filter == "Last 7 days":
            catalog_date_clause = "AND c.catalog_updated_at >= DATEADD('day', -7, CURRENT_TIMESTAMP)"
        elif catalog_date_filter == "Last 30 days":
            catalog_date_clause = "AND c.catalog_updated_at >= DATEADD('day', -30, CURRENT_TIMESTAMP)"
        elif catalog_date_filter == "Last 90 days":
            catalog_date_clause = "AND c.catalog_updated_at >= DATEADD('day', -90, CURRENT_TIMESTAMP)"
        elif catalog_date_filter == "Never updated":
            catalog_date_clause = "AND c.catalog_updated_at IS NULL"
        elif catalog_date_filter == "Custom range" and catalog_start and catalog_end:
            catalog_date_clause = f"AND c.catalog_updated_at BETWEEN '{catalog_start}' AND '{catalog_end}'"

        # Build days pending filter
        days_pending_clause = ""
        if max_days_pending is not None:
            days_pending_clause = f"AND DATEDIFF('day', b.updated_at, CURRENT_TIMESTAMP) <= {max_days_pending}"

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
              {bsku_date_clause}
          )
          WHERE rn = 1
        ),

        catalog_current AS (
          SELECT
            business_msid,
            catalog_photo_url,
            catalog_updated_at,
            catalog_updated_by,
            item_name
          FROM (
            SELECT
              CONCAT(business_id, '_', item_merchant_supplied_id) AS business_msid,
              photo_url AS catalog_photo_url,
              mpc_updated_at AS catalog_updated_at,
              mpc_updated_by AS catalog_updated_by,
              item_name,
              ROW_NUMBER() OVER (
                PARTITION BY business_id, item_merchant_supplied_id
                ORDER BY mpc_updated_at DESC NULLS LAST
              ) AS rn
            FROM x360.prod.merchant_catalog
            WHERE business_id IN ('{merchant_ids}')
          )
          WHERE rn = 1
        )

        SELECT DISTINCT
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
        WHERE 1=1
          AND (
            (c.business_msid IS NULL) OR
            (COALESCE(TRIM(b.bsku_photo_url), '') != COALESCE(TRIM(c.catalog_photo_url), '')
             AND b.updated_at > COALESCE(c.catalog_updated_at, '1900-01-01'))
          )
          {catalog_date_clause}
          {days_pending_clause}
        ORDER BY b.updated_at DESC, b.business_msid
        """

        return execute_query(query)

    # Load data and store in session state
    # Create a cache key based on query parameters
    query_key = f"{','.join(sorted(selected_merchants))}_{msid_filter_list}_{bsku_date_filter}_{catalog_date_filter}_{days_pending_filter}"

    # Check if we need to run the query or can use cached results
    if 'last_query_key' not in st.session_state or st.session_state.last_query_key != query_key:
        with st.spinner("🔍 Querying pending photo updates..."):
            df = get_pending_updates(
                selected_merchants,
                msid_filter_list,
                bsku_date_filter,
                bsku_start_date,
                bsku_end_date,
                catalog_date_filter,
                catalog_start_date,
                catalog_end_date,
                days_pending_filter
            )
            # Store results in session state
            st.session_state.query_results_a = df
            st.session_state.last_query_key = query_key
    else:
        # Use cached results
        df = st.session_state.query_results_a

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

        st.info("""
        📝 **Use Case A - Two-step workflow:**
        1. **Step 1 (fetch_photo_metadata)**: Upload URLs to create photo IDs
        2. **Step 2 (update_product_item)**: Use "Process Photo ID Output Files" section above to upload photo IDs to catalog
        """)

        # Prepare download data in correct format for fetch_photo_metadata
        download_df = filtered_df[['BUSINESS_ID', 'MERCHANT_SUPPLIED_ITEM_ID', 'NEW_PHOTO_URL']].copy()
        download_df.columns = ['businessId', 'itemMerchantSuppliedId', 'URL']

        # Add leading underscore to MSID to preserve leading zeros in Excel
        download_df['itemMerchantSuppliedId'] = '_' + download_df['itemMerchantSuppliedId'].astype(str)

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
                # Use QUOTE_ALL to preserve leading zeros in IDs
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

        # ============================================
        # MCP BULK TOOLS INTEGRATION
        # ============================================
        st.markdown("---")
        st.subheader("📤 Open in Bulk Tools (Automated)")

        if MCP_AVAILABLE:
            st.info("✅ MCP integration available - Click below to automatically open Bulk Tools with your CSV pre-loaded")

            if st.button("🚀 Open in Bulk Tools", type="primary", key="bulk_tools_usecase_a"):
                with st.spinner("Preparing CSV and opening Bulk Tools..."):
                    try:
                        # Save CSV to temporary file
                        temp_dir = Path(tempfile.gettempdir()) / "photo_updates"
                        temp_dir.mkdir(exist_ok=True)

                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        temp_csv_path = temp_dir / f"photo_updates_{timestamp}.csv"

                        st.write(f"DEBUG: Saving CSV to {temp_csv_path}")

                        # Save the first file (or combined if multiple)
                        download_df.to_csv(temp_csv_path, index=False)

                        st.write(f"DEBUG: CSV saved. Calling validate_and_open with category={BULK_CATEGORY_RETAIL_CATALOG}, operation={BULK_OPERATION_FETCH_PHOTO}")
                        st.info("ℹ️ Use Case A uses URLs from BSKU. First, create photo IDs using fetch_photo_metadata, then upload those photo IDs to catalog.")

                        # Call MCP to validate and open
                        # Use Case A has URLs (not photo IDs), so use fetch_photo_metadata
                        result = validate_and_open(
                            csv_path=str(temp_csv_path),
                            category_id=BULK_CATEGORY_RETAIL_CATALOG,
                            operation_id=BULK_OPERATION_FETCH_PHOTO
                        )

                        st.success(f"""
                        ✅ Success! Browser opened with Bulk Tools (fetch_photo_metadata)
                        - Operation: {result['category_id']}/{result['operation_id']}
                        - CSV pre-loaded in browser
                        - File saved at: {temp_csv_path}
                        """)

                        st.warning("""
                        📝 **Two-step workflow for Use Case A:**
                        1. **Current step**: Submit this CSV in Bulk Tools to create photo IDs from URLs
                        2. **Next step**: Download the photo ID output, then use the "Process Photo ID Output Files" section at the top of this dashboard to upload those photo IDs to the catalog
                        """)

                    except FileNotFoundError as e:
                        st.error(f"""
                        ❌ MCP Server not found

                        Please install Bulk Tools MCP first:
                        ```bash
                        git clone https://github.com/doordash/nv-operator-tooling-poc.git /tmp/nv-operator-tooling-poc
                        bash /tmp/nv-operator-tooling-poc/bulk-tools-mcp/scripts/install.sh
                        ```

                        Error details: {str(e)}
                        """)

                    except Exception as e:
                        import traceback
                        error_details = traceback.format_exc()
                        st.error(f"""
                        ❌ Error opening Bulk Tools

                        Error: {str(e)}

                        Full traceback:
                        ```
                        {error_details}
                        ```

                        You can still download the CSV manually above and upload it to Bulk Tools.
                        """)
        else:
            st.warning(f"""
            ⚠️ MCP integration not available

            {f'Error: {MCP_ERROR}' if MCP_ERROR else ''}

            To enable automatic Bulk Tools opening, install the Bulk Tools MCP:
            ```bash
            git clone https://github.com/doordash/nv-operator-tooling-poc.git /tmp/nv-operator-tooling-poc
            bash /tmp/nv-operator-tooling-poc/bulk-tools-mcp/scripts/install.sh
            ```

            For now, download the CSV above and upload manually to Bulk Tools.
            """)

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
# USE CASE B: RED BUILD ITEM NAME MATCH QUERY
# ============================================
elif use_case == "Use Case B: Red Build Item Name Match Query":
    st.subheader("🔴 Red Build Item Name Match Query")
    st.markdown("Query items with matched photo URLs from Red Build vendor data.")

    # Button to run query
    if st.button("🚀 Run Red Build Query", type="primary"):
        with st.spinner("Querying Snowflake..."):
            # Execute Red Build query
            red_build_query = """
            SELECT
              x360.UMP_PRODUCT_CATEGORY_L1_ID,
              x360.dd_sic_v2,
              x360.business_id,
              x360.item_merchant_supplied_id AS x360_msid,
              x360.business_id || '-' || x360.item_merchant_supplied_id AS bmsid,
              x360.item_name AS x360_item_name,
              x360.photo_id AS x360_photo_id,
              red.PHOTO_ID AS red_build_photo_id,
              red.IMAGE_URL AS FINAL_IMAGE_URLS,
              red.match_decision,
              red.confidence,
              p.PHOTO_UUID
            FROM x360.prod.merchant_catalog AS x360
            INNER JOIN proddb.static.NVRedbuildPhotos AS red
              ON red.BMSID = x360.business_id::VARCHAR || '-' || x360.item_merchant_supplied_id::VARCHAR
             AND red.IMAGE_URL IS NOT NULL
             AND red.confidence = 'High'
             AND red.match_decision = 'YES'
            LEFT JOIN PHOTO_SERVICE_PROD.PUBLIC.PHOTO AS p
              ON p.origin_photo_id = red.PHOTO_ID
            WHERE x360.dd_sic_v2 IS NOT NULL
              AND x360.photo_id IN ('4892685', '34848455')
            QUALIFY ROW_NUMBER() OVER (
              PARTITION BY x360.business_id, x360.item_merchant_supplied_id
              ORDER BY red.PHOTO_ID
            ) = 1
            """

            df_red_build = execute_query(red_build_query)

            # Store results in session state
            st.session_state.query_results_b = df_red_build

    # Check if we have cached results from a previous run
    if 'query_results_b' in st.session_state:
        df_red_build = st.session_state.query_results_b

        if len(df_red_build) > 0:
            st.success(f"✅ Found {len(df_red_build):,} items with matched Red Build photos")

            # Display summary metrics
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            with col_metric1:
                st.metric("Total Items", f"{len(df_red_build):,}")
            with col_metric2:
                st.metric("Unique Merchants", len(df_red_build['BUSINESS_ID'].unique()))
            with col_metric3:
                st.metric("Unique Categories", len(df_red_build['DD_SIC_V2'].dropna().unique()))

            # Preview data
            st.markdown("---")
            st.subheader("📊 Red Build Data Preview")
            with st.expander("👁️ View Data (first 100 rows)", expanded=True):
                st.dataframe(df_red_build.head(100), use_container_width=True, hide_index=True)

            # ============================================
            # DOWNLOAD FUNCTIONALITY
            # ============================================
            st.markdown("---")
            st.subheader("⬇️ Download CSV for Bulk Upload")

            st.info("""
            ✅ **Use Case B - Direct catalog update:**
            Red Build vendor photos already have photo IDs, so this CSV will directly update the merchant catalog using `update_product_item`.
            """)

            # Prepare download data in correct format for update_product_item
            download_df = df_red_build[['BUSINESS_ID', 'X360_MSID', 'RED_BUILD_PHOTO_ID']].copy()
            download_df.columns = ['businessId', 'itemMerchantSuppliedId', 'photoId']

            # Add leading underscore to MSID to preserve leading zeros in Excel
            download_df['itemMerchantSuppliedId'] = '_' + download_df['itemMerchantSuppliedId'].astype(str)

            # update_product_item only needs these 3 columns
            download_df = download_df[['businessId', 'itemMerchantSuppliedId', 'photoId']]

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
                        file_name=f"red_build_photo_updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
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

                            filename = f"red_build_photo_updates_part{i+1}_of_{num_files}.csv"
                            zip_file.writestr(filename, csv_data)

                    zip_data = zip_buffer.getvalue()

                    st.download_button(
                        label=f"📦 Download ZIP ({num_files} files, {total_rows:,} rows)",
                        data=zip_data,
                        file_name=f"red_build_photo_updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip",
                        type="primary",
                        use_container_width=True
                    )

            with col_download2:
                # Preview download format
                with st.expander("👁️ Preview Download Format"):
                    st.dataframe(download_df.head(10), use_container_width=True, hide_index=True)

            # ============================================
            # MCP BULK TOOLS INTEGRATION
            # ============================================
            st.markdown("---")
            st.subheader("📤 Open in Bulk Tools (Automated)")

            if MCP_AVAILABLE:
                st.info("✅ MCP integration available - Click below to automatically open Bulk Tools with your CSV pre-loaded")

                if st.button("🚀 Open in Bulk Tools", type="primary", key="bulk_tools_usecase_b"):
                    with st.spinner("Preparing CSV and opening Bulk Tools..."):
                        try:
                            # Save CSV to temporary file
                            temp_dir = Path(tempfile.gettempdir()) / "photo_updates"
                            temp_dir.mkdir(exist_ok=True)

                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            temp_csv_path = temp_dir / f"red_build_photo_updates_{timestamp}.csv"

                            st.write(f"DEBUG: Saving CSV to {temp_csv_path}")

                            # Save the first file (or combined if multiple)
                            download_df.to_csv(temp_csv_path, index=False)

                            st.write(f"DEBUG: CSV saved. Calling validate_and_open with category={BULK_CATEGORY_RETAIL_CATALOG}, operation={BULK_OPERATION_UPDATE_CATALOG}")

                            # Call MCP to validate and open
                            result = validate_and_open(
                                csv_path=str(temp_csv_path),
                                category_id=BULK_CATEGORY_RETAIL_CATALOG,
                                operation_id=BULK_OPERATION_UPDATE_CATALOG
                            )

                            st.success(f"""
                            ✅ Success! Browser opened with Bulk Tools (update_product_item)
                            - Operation: {result['category_id']}/{result['operation_id']}
                            - CSV with photo IDs pre-loaded in browser
                            - File saved at: {temp_csv_path}
                            """)

                            st.info("👉 Review the photo IDs in your browser, then click **Submit** to update the catalog")

                        except FileNotFoundError as e:
                            st.error(f"""
                            ❌ MCP Server not found

                            Please install Bulk Tools MCP first:
                            ```bash
                            git clone https://github.com/doordash/nv-operator-tooling-poc.git /tmp/nv-operator-tooling-poc
                            bash /tmp/nv-operator-tooling-poc/bulk-tools-mcp/scripts/install.sh
                            ```

                            Error details: {str(e)}
                            """)

                        except Exception as e:
                            import traceback
                            error_details = traceback.format_exc()
                            st.error(f"""
                            ❌ Error opening Bulk Tools

                            Error: {str(e)}

                            Full traceback:
                            ```
                            {error_details}
                            ```

                            You can still download the CSV manually above and upload it to Bulk Tools.
                            """)
            else:
                st.warning("""
                ⚠️ MCP integration not available

                To enable automatic Bulk Tools opening, install the Bulk Tools MCP:
                ```bash
                git clone https://github.com/doordash/nv-operator-tooling-poc.git /tmp/nv-operator-tooling-poc
                bash /tmp/nv-operator-tooling-poc/bulk-tools-mcp/scripts/install.sh
                ```

                For now, download the CSV above and upload manually to Bulk Tools.
                """)

            st.markdown("---")
            st.info("""
            💡 **How it works:**
            - Queries x360 catalog matched with Red Build vendor photo URLs
            - Only includes high-confidence YES matches from vendor
            - Download CSV with format: businessId, itemMerchantSuppliedId, URL, angle, source
            - Upload to bulk tool to update catalog with vendor-matched photos
            """)

        else:
            st.warning("⚠️ No Red Build matched items found in the database.")
            st.info("💡 The NVRedbuildPhotos table may need to be updated with new vendor data.")

    else:
        st.info("👆 Click 'Run Red Build Query' to fetch matched vendor photos")

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Dashboard v2.0")
