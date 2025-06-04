# Set page config
import streamlit as st

st.set_page_config(
    page_title="Master App Tim Kandang",
    layout="wide",
    initial_sidebar_state="expanded"
)

import pandas as pd
import plotly.express as px
from datetime import datetime
from sheets_helper import GoogleHelper
from config_helper import ConfigHelper
from environment_helper import get_environment_helper

# Initialize environment helper (cached)
env_helper = get_environment_helper()

# Validate required secrets for current environment
required_secrets = [
    "google.credentials_file",
    "google.spreadsheet_id"
]

if not env_helper.validate_required_secrets(required_secrets):
    st.stop()

# Get configuration from environment helper
GOOGLE_CREDENTIALS_FILE = env_helper.get_credentials_file()
SPREADSHEET_ID = env_helper.get_spreadsheet_id()
debug_mode = env_helper.is_debug_mode()

# Initialize configuration helper
@st.cache_resource
def init_config():
    return ConfigHelper()

# Initialize Google helper
@st.cache_resource
def init_helper():
    return GoogleHelper(GOOGLE_CREDENTIALS_FILE)

# Initialize configuration
config = init_config()

# Show environment info
env_helper.show_environment_info(show_in_sidebar=True)

# Title
st.title("Master App Tim Kandang")

# Show debug mode indicator
if debug_mode:
    st.warning("🧪 Running in DEBUG mode")
    # Set debug flag for sheets_helper
    st.session_state._debug_mode = True
else:
    st.session_state._debug_mode = False

# Main welcome content
st.markdown("""
### Selamat datang di sistem manajemen kandang Qurban Plus 1446

Sistem ini membantu Anda mengelola:
- 📥 **Data Masuk Hewan** (Form Masuk)
- 📤 **Data Keluar Hewan** (Form Keluar)

Silakan gunakan menu di sidebar untuk navigasi.
""")

# Get sheet ranges from config
INBOUND_RANGE = config.get_sheet_range("inbound")
OUTBOUND_RANGE = config.get_sheet_range("outbound")

# Get global column names that are used in multiple functions
quantity_col = config.get_column_name("inbound", 5)  # "Quantity" column for inbound data

st.header("Dashboard Manajemen Qurban")

# Initialize helper
helper = init_helper()

# Load data
inbound_df = helper.get_records(SPREADSHEET_ID, INBOUND_RANGE)
outbound_df = helper.get_records(SPREADSHEET_ID, OUTBOUND_RANGE)

# Get column names from config
inbound_columns = config.get_sheet_columns("inbound")
outbound_columns = config.get_sheet_columns("outbound")

# Create navigation tabs
tab1, tab2 = st.tabs(["📊 Ringkasan Stok", "📦 Status Pesanan"])

def create_daily_progress_table(inbound_df, supplier_filter=None, animal_filter=None, status_filter=None):
    """Create daily progress table showing delivery quantities by date - text format"""
    if inbound_df.empty:
        return None
    
    try:
        # Get proper column names from config
        supplier_col = config.get_column_name("inbound", 3)      # "Supplier"
        animal_type_col = config.get_column_name("inbound", 2)   # "Tipe Hewan"
        variant_col = config.get_column_name("inbound", 4)       # "Varian"
        quantity_col = config.get_column_name("inbound", 5)      # "Quantity"
        date_col = config.get_column_name("inbound", 10)         # "Tanggal Pengiriman"
        timestamp_col = config.get_column_name("inbound", 0)     # "Timestamp"
        
        # Check if required columns exist
        if not quantity_col or quantity_col not in inbound_df.columns:
            return None
        
        # Create copy for filtering
        filtered_df = inbound_df.copy()
        
        # Apply filters
        if supplier_filter and supplier_filter != "Semua" and supplier_col and supplier_col in filtered_df.columns:
            filtered_df = filtered_df[filtered_df[supplier_col] == supplier_filter]
        
        if animal_filter and animal_filter != "Semua" and animal_type_col and animal_type_col in filtered_df.columns:
            # Handle both general animal (like "Domba/Kambing") and specific variant filtering
            if animal_filter in ["Domba/Kambing", "Sapi"]:
                # General animal filter
                filtered_df = filtered_df[filtered_df[animal_type_col] == animal_filter]
            else:
                # Specific variant filter - use variant column if available
                if variant_col and variant_col in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df[variant_col] == animal_filter]
        
        if filtered_df.empty:
            return None
        
        # Use delivery date if available, otherwise use timestamp
        date_column_to_use = date_col if date_col and date_col in filtered_df.columns and not filtered_df[date_col].isna().all() else timestamp_col
        
        if not date_column_to_use or date_column_to_use not in filtered_df.columns:
            return None
            
        # Convert to datetime and extract date part
        filtered_df['date'] = pd.to_datetime(filtered_df[date_column_to_use], errors='coerce').dt.date
        
        # Remove rows with invalid dates
        filtered_df = filtered_df.dropna(subset=['date'])
        
        if filtered_df.empty:
            return None
        
        # Convert quantity to numeric before summing
        filtered_df[quantity_col] = pd.to_numeric(filtered_df[quantity_col], errors='coerce').fillna(0)
        
        # Group by date and sum quantities
        daily_totals = filtered_df.groupby('date')[quantity_col].sum().reset_index()
        daily_totals = daily_totals.sort_values('date')
        
        if daily_totals.empty:
            return None
        
        # Convert to text format instead of dataframe table
        if len(daily_totals) <= 10:  # Show all if 10 or fewer dates
            for _, row in daily_totals.iterrows():
                date_str = row['date'].strftime('%d/%m') if hasattr(row['date'], 'strftime') else str(row['date'])
                st.markdown(f"**{date_str}** | {int(row[quantity_col])} ekor", unsafe_allow_html=True)
        else:
            # Show recent dates
            recent_dates = daily_totals.tail(10)  # Show last 10 dates
            for _, row in recent_dates.iterrows():
                date_str = row['date'].strftime('%d/%m') if hasattr(row['date'], 'strftime') else str(row['date'])
                st.markdown(f"**{date_str}** | {int(row[quantity_col])} ekor", unsafe_allow_html=True)
        
        return True  # Indicate successful rendering
        
    except Exception as e:
        if debug_mode:
            st.error(f"Error in daily progress: {str(e)}")
        return None

def process_order_data(inbound_df, outbound_df, selected_animal=None):
    """Process inbound data to create order summaries with expected quantities and outbound data"""
    if inbound_df.empty:
        inbound_processed = pd.DataFrame()
    else:
        # Get column names
        animal_type_col = config.get_column_name("inbound", 2)  # "Tipe Hewan"
        supplier_col = config.get_column_name("inbound", 3)     # "Supplier"
        variant_col = config.get_column_name("inbound", 4)      # "Varian"
        quantity_col = config.get_column_name("inbound", 5)     # "Quantity"
        date_col = config.get_column_name("inbound", 10)        # "Tanggal Pengiriman"
        timestamp_col = config.get_column_name("inbound", 0)    # "Timestamp"
        
        if not all([animal_type_col, supplier_col, variant_col, quantity_col]):
            inbound_processed = pd.DataFrame()
        else:
            try:
                # Clean and prepare data
                df_clean = inbound_df.copy()
                df_clean[quantity_col] = pd.to_numeric(df_clean[quantity_col], errors='coerce').fillna(0)
                
                # Filter by selected animal if specified
                if selected_animal and selected_animal != "Semua":
                    df_clean = df_clean[df_clean[animal_type_col] == selected_animal]

                # Group by supplier, animal type, and variant to create delivery summaries
                delivery_summary = df_clean.groupby([
                    supplier_col, 
                    animal_type_col, 
                    variant_col
                ]).agg({
                    quantity_col: 'sum',
                    timestamp_col: 'count'  # Count deliveries
                }).reset_index()
                
                delivery_summary.columns = [
                    'supplier', 'animal_type', 'variant', 
                    'total_delivered', 'delivery_count'
                ]
                
                inbound_processed = delivery_summary
                
            except (KeyError, AttributeError) as e:
                if debug_mode:
                    st.error(f"Error processing inbound data: {e}")
                inbound_processed = pd.DataFrame()
    
    # Process outbound data for "Keluar" metric
    outbound_totals = {}
    if not outbound_df.empty:
        try:
            animal_type_col_out = config.get_column_name("outbound", 1)  # "Tipe Hewan"
            quantity_col_out = config.get_column_name("outbound", 3)     # "Quantity"
            
            if animal_type_col_out and quantity_col_out:
                df_out_clean = outbound_df.copy()
                df_out_clean[quantity_col_out] = pd.to_numeric(df_out_clean[quantity_col_out], errors='coerce').fillna(0)
                
                # Filter by selected animal if specified
                if selected_animal and selected_animal != "Semua":
                    df_out_clean = df_out_clean[df_out_clean[animal_type_col_out] == selected_animal]
                
                # Group by animal type for outbound totals
                outbound_summary = df_out_clean.groupby(animal_type_col_out)[quantity_col_out].sum()
                outbound_totals = outbound_summary.to_dict()
                
        except (KeyError, AttributeError) as e:
            if debug_mode:
                st.error(f"Error processing outbound data: {e}")
    
    # Add order data from config and outbound data
    order_data = []
    if not inbound_processed.empty:
        for _, row in inbound_processed.iterrows():
            ordered_qty = config.get_order_data_for_supplier_and_category(
                row['animal_type'], 
                row['supplier'], 
                row['variant']
            )
            
            # Get outbound quantity for this animal type
            outbound_qty = outbound_totals.get(row['animal_type'], 0)
            
            order_data.append({
                'supplier': row['supplier'],
                'animal_type': row['animal_type'],
                'variant': row['variant'],
                'ordered_quantity': ordered_qty,
                'total_delivered': row['total_delivered'],
                'total_outbound': outbound_qty,
                'remaining_quantity': max(0, ordered_qty - row['total_delivered']),
                'delivery_count': row['delivery_count'],
                'completion_rate': (row['total_delivered'] / ordered_qty * 100) if ordered_qty > 0 else 0
            })
    
    # Also add orders that haven't had any deliveries yet
    all_orders = config.get_animal_orders()
    existing_combinations = set((row['supplier'], row['animal_type'], row['variant']) 
                              for row in order_data)
    
    for animal_key in ['Domba', 'Sapi']:
        animal_type = 'Domba/Kambing' if animal_key == 'Domba' else 'Sapi'
        
        # Skip if we're filtering for a specific animal and this doesn't match
        if selected_animal and selected_animal != "Semua" and animal_type != selected_animal:
            continue
        
        for order in all_orders.get(animal_key, []):
            category = order['category']
            vendors = order.get('vendors', {})
            
            for vendor, qty in vendors.items():
                if vendor and qty > 0:  # Skip empty vendors
                    # Check if this combination already exists in delivered data
                    combo = (vendor, animal_type, category)
                    if combo not in existing_combinations:
                        # Get outbound quantity for this animal type
                        outbound_qty = outbound_totals.get(animal_type, 0)
                        
                        order_data.append({
                            'supplier': vendor,
                            'animal_type': animal_type,
                            'variant': category,
                            'ordered_quantity': qty,
                            'total_delivered': 0,
                            'total_outbound': outbound_qty,
                            'remaining_quantity': qty,
                            'delivery_count': 0,
                            'completion_rate': 0
                        })
    
    return pd.DataFrame(order_data)

with tab1:
    # Original dashboard content
    # Process data for goats and cows separately
    def process_animal_data(df, animal_type, sheet_type):
        if df.empty:
            return 0
            
        # Get column names from config
        if sheet_type == "inbound":
            animal_type_col = config.get_column_name("inbound", 2)  # "Tipe Hewan"
            quantity_col = config.get_column_name("inbound", 5)     # "Quantity"
        else:  # outbound
            animal_type_col = config.get_column_name("outbound", 1)  # "Tipe Hewan"  
            quantity_col = config.get_column_name("outbound", 3)     # "Quantity"
        
        if not animal_type_col or not quantity_col:
            return 0
            
        # Filter by animal type
        try:
            animal_df = df[df[animal_type_col] == animal_type]
            if animal_df.empty:
                return 0
            
            return pd.to_numeric(animal_df[quantity_col], errors='coerce').fillna(0).sum()
        except (KeyError, AttributeError):
            return 0

    # Calculate totals
    if not inbound_df.empty or not outbound_df.empty:
        # Debug: Show what animal types we have in the data
        if not inbound_df.empty:
            animal_col = config.get_column_name("inbound", 2)
            if animal_col and animal_col in inbound_df.columns:
                unique_animals = inbound_df[animal_col].unique()
        
        st.subheader("Ringkasan Stok")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Domba/Kambing")
            goats_in = process_animal_data(inbound_df, "Domba/Kambing", "inbound")
            goats_out = process_animal_data(outbound_df, "Domba/Kambing", "outbound")
            goats_stock = goats_in - goats_out
            
            st.metric("Total Masuk", f"{int(goats_in)} ekor")
            st.metric("Total Keluar", f"{int(goats_out)} ekor")
            st.metric("Stok Saat Ini", f"{int(goats_stock)} ekor")
            
        with col2:
            st.markdown("##### Sapi")
            cows_in = process_animal_data(inbound_df, "Sapi", "inbound")
            cows_out = process_animal_data(outbound_df, "Sapi", "outbound")
            cows_stock = cows_in - cows_out
            
            st.metric("Total Masuk", f"{int(cows_in)} ekor")
            st.metric("Total Keluar", f"{int(cows_out)} ekor")
            st.metric("Stok Saat Ini", f"{int(cows_stock)} ekor")
        
        # Overall progress percentage
        st.markdown("---")
        st.markdown("##### Progress Keseluruhan")
        
        # Calculate overall progress from order data
        order_data_for_progress = process_order_data(inbound_df, outbound_df)
        if not order_data_for_progress.empty:
            total_ordered_all = order_data_for_progress['ordered_quantity'].sum()
            total_delivered_all = order_data_for_progress['total_delivered'].sum()
            overall_completion = (total_delivered_all / total_ordered_all * 100) if total_ordered_all > 0 else 0
            
            # Progress color
            if overall_completion == 0:
                overall_progress_color = "#dc3545"  # Red
            elif overall_completion < 50:
                overall_progress_color = "#ffc107"  # Yellow
            else:
                overall_progress_color = "#198754"  # Green
            
            st.progress(overall_completion / 100)
            st.markdown(f"<div style='text-align: center; margin-top: -10px;'><h2 style='margin: 0; color: {overall_progress_color};'>{overall_completion:.1f}% selesai</h2></div>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Dipesan", f"{int(total_ordered_all)} ekor")
            with col2:
                st.metric("Total Diterima", f"{int(total_delivered_all)} ekor")
            with col3:
                st.metric("Sisa Pesanan", f"{int(total_ordered_all - total_delivered_all)} ekor")
        
        # Progress Harian section
        st.markdown("---")
        st.markdown("#### 📈 Progress Harian")
        
        # Get daily progress data
        daily_progress_data = {}
        try:
            if not inbound_df.empty:
                quantity_col = config.get_column_name("inbound", 5)      # "Quantity"
                date_col = config.get_column_name("inbound", 10)         # "Tanggal Pengiriman"
                timestamp_col = config.get_column_name("inbound", 0)     # "Timestamp"
                
                if quantity_col and quantity_col in inbound_df.columns:
                    filtered_df = inbound_df.copy()
                    date_column_to_use = date_col if date_col and date_col in filtered_df.columns and not filtered_df[date_col].isna().all() else timestamp_col
                    
                    if date_column_to_use and date_column_to_use in filtered_df.columns:
                        filtered_df['date'] = pd.to_datetime(filtered_df[date_column_to_use], errors='coerce').dt.date
                        filtered_df = filtered_df.dropna(subset=['date'])
                        
                        if not filtered_df.empty:
                            filtered_df[quantity_col] = pd.to_numeric(filtered_df[quantity_col], errors='coerce').fillna(0)
                            daily_totals = filtered_df.groupby('date')[quantity_col].sum().reset_index()
                            daily_totals = daily_totals.sort_values('date')
                            
                            for _, row in daily_totals.iterrows():
                                date_str = row['date'].strftime('%d/%m') if hasattr(row['date'], 'strftime') else str(row['date'])
                                daily_progress_data[date_str] = int(row[quantity_col])
        except:
            pass
        
        # Create horizontal bar chart
        target_dates = ["02/06", "03/06", "04/06", "05/06", "06/06", "07/06", "08/06"]
        quantities = [daily_progress_data.get(date, 0) for date in target_dates]
        
        # Create horizontal bar chart using plotly with reversed axes
        fig = px.bar(
            y=quantities,
            x=target_dates,
            orientation='v',
            labels={'y': 'Jumlah (ekor)', 'x': 'Tanggal'},
            title='Progress Harian Pengiriman'
        )
        
        # Update layout for better visualization
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False
        )
        
        # Display the chart
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Belum ada data yang tercatat. Silakan mulai dengan mencatat hewan masuk.")

with tab2:
    # New Order Tracking View with general animal selector
    st.subheader("📦 Status Pesanan dan Pengiriman")
    
    # General animal selector at the top
    st.markdown("### Pilih Jenis Hewan")
    selected_general_animal = st.selectbox(
        "Jenis hewan yang ingin dilihat:",
        ["Semua", "Domba/Kambing", "Sapi"]
    )
    
    st.markdown("---")
    
    def get_status_color(delivered, ordered):
        """Get color based on delivery completion rate"""
        if ordered == 0:
            return "⚫"  # No order data
        
        completion_rate = delivered / ordered
        if completion_rate >= 1.0:
            return "🟢"  # Complete (100%+)
        elif completion_rate >= 0.8:
            return "🟡"  # Near complete (80%+)
        elif completion_rate >= 0.5:
            return "🟠"  # Partial (50%+)
        elif completion_rate > 0:
            return "🔴"  # Started but low
        else:
            return "⚪"  # Not started
    
    def render_order_card(supplier, animal_type, variant, ordered_qty, delivered_qty, outbound_qty, remaining_qty, delivery_count, completion_rate, inbound_df, selected_general_animal):
        """Render enhanced order card using Streamlit native components with text instead of tables"""
        
        status_icon = get_status_color(delivered_qty, ordered_qty)
        
        # Determine progress color (green-based with red for 0%)
        if completion_rate == 0:
            progress_color = "#dc3545"  # Red for 0%
        elif completion_rate < 25:
            progress_color = "#fd7e14"  # Orange for low progress
        elif completion_rate < 50:
            progress_color = "#ffc107"  # Yellow for medium-low
        elif completion_rate < 75:
            progress_color = "#20c997"  # Teal for medium-high
        else:
            progress_color = "#198754"  # Green for high progress
        
        # Format title with title case
        def title_case(text):
            return ' '.join(word.capitalize() for word in text.split())
        
        formatted_supplier = title_case(supplier)
        formatted_variant = title_case(variant)
        
        # Use Streamlit container with custom CSS
        with st.container():
            # Card content using Streamlit components
            with st.container():
                # Header row - supplier | variant format with title case, lower heading level
                st.markdown(f"##### {status_icon} {formatted_supplier} | {formatted_variant}")
                
                # Progress bar with bigger percentage and green-based coloring
                progress_value = min(1.0, max(0.0, completion_rate / 100))
                st.progress(progress_value)
                st.markdown(f"<div style='text-align: center; margin-top: -10px;'><h2 style='margin: 0; color: {progress_color};'>{completion_rate:.1f}% selesai</h2></div>", unsafe_allow_html=True)
                
                # Metrics as text in columns instead of table
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Dipesan", int(ordered_qty))
                
                with col2:
                    st.metric("Diterima", int(delivered_qty))
                
                with col3:
                    st.metric("Sisa", int(remaining_qty))

                st.markdown("---")
    
    def render_vendor_summary_card(supplier, animal_type, filtered_data, inbound_df, selected_general_animal):
        """Render vendor summary card with kedatangan info"""
        
        # Calculate totals for this vendor
        vendor_data = filtered_data[filtered_data['supplier'] == supplier]
        if animal_type != "Semua":
            vendor_data = vendor_data[vendor_data['animal_type'] == animal_type]
        
        total_ordered = vendor_data['ordered_quantity'].sum()
        total_delivered = vendor_data['total_delivered'].sum()
        total_outbound = vendor_data['total_outbound'].sum()
        total_remaining = vendor_data['remaining_quantity'].sum()
        total_delivery_count = vendor_data['delivery_count'].sum()
        completion_rate = (total_delivered / total_ordered * 100) if total_ordered > 0 else 0
        
        # Determine status
        status_icon = get_status_color(total_delivered, total_ordered)
        
        # Determine progress color (green-based with red for 0%)
        if completion_rate == 0:
            progress_color = "#dc3545"  # Red for 0%
        elif completion_rate < 25:
            progress_color = "#fd7e14"  # Orange for low progress
        elif completion_rate < 50:
            progress_color = "#ffc107"  # Yellow for medium-low
        elif completion_rate < 75:
            progress_color = "#20c997"  # Teal for medium-high
        else:
            progress_color = "#198754"  # Green for high progress
        
        # Format title with title case
        def title_case(text):
            return ' '.join(word.capitalize() for word in text.split())
        
        formatted_supplier = title_case(supplier)
        
        with st.container():
            # Header - supplier only, title case, no caps
            st.markdown(f"#### {status_icon} {formatted_supplier}")
            
            # Progress bar with bigger percentage and green-based coloring
            progress_value = min(1.0, max(0.0, completion_rate / 100))
            st.progress(progress_value)
            st.markdown(f"<div style='text-align: center; margin-top: -10px;'><h2 style='margin: 0; color: {progress_color};'>{completion_rate:.1f}% selesai</h2></div>", unsafe_allow_html=True)
            
            # Metrics using st.metric for better visualization
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Dipesan", f"{int(total_ordered)} ekor")
            
            with col2:
                st.metric("Diterima", f"{int(total_delivered)} ekor")
            
            with col3:
                st.metric("Sisa", f"{int(total_remaining)} ekor")
            
            st.markdown("---")
    
    def get_daily_arrivals(inbound_df, supplier=None, animal_type=None, variant=None, selected_animal=None):
        """Get daily arrival data for supplier and/or category"""
        if inbound_df.empty:
            return pd.DataFrame()
        
        try:
            # Get column names
            animal_type_col = config.get_column_name("inbound", 2)  # "Tipe Hewan"
            supplier_col = config.get_column_name("inbound", 3)     # "Supplier"
            variant_col = config.get_column_name("inbound", 4)      # "Varian"
            quantity_col = config.get_column_name("inbound", 5)     # "Quantity"
            date_col = config.get_column_name("inbound", 10)        # "Tanggal Pengiriman"
            timestamp_col = config.get_column_name("inbound", 0)    # "Timestamp"
            
            # Clean data
            df_clean = inbound_df.copy()
            df_clean[quantity_col] = pd.to_numeric(df_clean[quantity_col], errors='coerce').fillna(0)
            
            # Filter by selected general animal
            if selected_animal and selected_animal != "Semua":
                df_clean = df_clean[df_clean[animal_type_col] == selected_animal]
            
            # Filter by supplier if specified
            if supplier and supplier != "Semua":
                df_clean = df_clean[df_clean[supplier_col] == supplier]
            
            # Filter by animal type if specified
            if animal_type and animal_type != "Semua":
                df_clean = df_clean[df_clean[animal_type_col] == animal_type]
            
            # Filter by variant if specified
            if variant:
                df_clean = df_clean[df_clean[variant_col] == variant]
            
            if df_clean.empty:
                return pd.DataFrame()
            
            # Extract date from delivery date or timestamp
            df_clean['date'] = pd.to_datetime(df_clean[date_col] if date_col and not df_clean[date_col].isna().all() else df_clean[timestamp_col], errors='coerce').dt.date
            
            # Group by date and sum quantities
            daily_data = df_clean.groupby('date')[quantity_col].sum().reset_index()
            daily_data.columns = ['date', 'quantity']
            
            # Sort by date descending to show latest first
            daily_data = daily_data.sort_values('date', ascending=False)
            
            return daily_data
            
        except (KeyError, AttributeError) as e:
            if debug_mode:
                st.error(f"Error processing daily arrivals: {e}")
            return pd.DataFrame()
    
    # Process and display orders
    if not inbound_df.empty or not outbound_df.empty:
        order_data = process_order_data(inbound_df, outbound_df, selected_general_animal)
        
        if not order_data.empty:
            # Filter controls - updated based on selected animal
            col1, col2, col3 = st.columns(3)
            
            with col1:
                suppliers = ['Semua'] + sorted(order_data['supplier'].unique().tolist())
                selected_supplier = st.selectbox("Filter Supplier", suppliers)
            
            with col2:
                # Use specific variants instead of high-level animal types
                if selected_general_animal == "Semua":
                    variants = ['Semua'] + sorted(order_data['variant'].unique().tolist())
                else:
                    # Filter variants based on selected general animal
                    filtered_variants = order_data[order_data['animal_type'] == selected_general_animal]['variant'].unique()
                    variants = ['Semua'] + sorted(filtered_variants.tolist())
                selected_variant = st.selectbox("Filter Varian", variants)
            
            with col3:
                status_options = ['Semua', '🟢 100%', '🟡 50-99%', '🔴 0-49%']
                selected_status = st.selectbox("Filter Status", status_options)
            
            # Apply filters
            filtered_data = order_data.copy()
            
            if selected_supplier != 'Semua':
                filtered_data = filtered_data[filtered_data['supplier'] == selected_supplier]
            
            # Use variant filter instead of animal type filter
            if selected_variant != 'Semua':
                filtered_data = filtered_data[filtered_data['variant'] == selected_variant]
            
            # Apply status filter
            if selected_status != 'Semua':
                if selected_status == '🟢 100%':
                    filtered_data = filtered_data[filtered_data['completion_rate'] >= 100]
                elif selected_status == '🟡 50-99%':
                    filtered_data = filtered_data[
                        (filtered_data['completion_rate'] >= 50) & 
                        (filtered_data['completion_rate'] < 100)
                    ]
                elif selected_status == '🔴 0-49%':
                    filtered_data = filtered_data[filtered_data['completion_rate'] < 50]
            
            # Display summary metrics in 2 columns
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total Pesanan", len(filtered_data))
                total_delivered = filtered_data['total_delivered'].sum()
                st.metric("Total Diterima", f"{int(total_delivered)} ekor")
            
            with col2:
                total_ordered = filtered_data['ordered_quantity'].sum()
                st.metric("Total Dipesan", f"{int(total_ordered)} ekor")
                total_remaining = filtered_data['remaining_quantity'].sum()
                completion_rate = (total_delivered / total_ordered * 100) if total_ordered > 0 else 0
                st.metric("Sisa Pesanan", f"{int(total_remaining)} ekor", 
                         delta=f"{completion_rate:.1f}% selesai")
            
            st.markdown("---")
            
            # Kedatangan Chart based on filters
            st.markdown("#### 📈 Progress Kedatangan")
            
            # Get kedatangan data based on filters
            kedatangan_data = {}
            try:
                if not inbound_df.empty:
                    quantity_col = config.get_column_name("inbound", 5)      # "Quantity"
                    supplier_col = config.get_column_name("inbound", 3)      # "Supplier"  
                    variant_col = config.get_column_name("inbound", 4)       # "Varian"
                    animal_type_col = config.get_column_name("inbound", 2)   # "Tipe Hewan"
                    date_col = config.get_column_name("inbound", 10)         # "Tanggal Pengiriman"
                    timestamp_col = config.get_column_name("inbound", 0)     # "Timestamp"
                    
                    if quantity_col and quantity_col in inbound_df.columns:
                        filtered_kedatangan_df = inbound_df.copy()
                        
                        # Apply same filters as the order display
                        if selected_supplier != 'Semua' and supplier_col and supplier_col in filtered_kedatangan_df.columns:
                            filtered_kedatangan_df = filtered_kedatangan_df[filtered_kedatangan_df[supplier_col] == selected_supplier]
                        
                        if selected_variant != 'Semua' and variant_col and variant_col in filtered_kedatangan_df.columns:
                            filtered_kedatangan_df = filtered_kedatangan_df[filtered_kedatangan_df[variant_col] == selected_variant]
                        
                        # Filter by selected general animal
                        if selected_general_animal != "Semua" and animal_type_col and animal_type_col in filtered_kedatangan_df.columns:
                            filtered_kedatangan_df = filtered_kedatangan_df[filtered_kedatangan_df[animal_type_col] == selected_general_animal]
                        
                        if not filtered_kedatangan_df.empty:
                            date_column_to_use = date_col if date_col and date_col in filtered_kedatangan_df.columns and not filtered_kedatangan_df[date_col].isna().all() else timestamp_col
                            
                            if date_column_to_use and date_column_to_use in filtered_kedatangan_df.columns:
                                filtered_kedatangan_df['date'] = pd.to_datetime(filtered_kedatangan_df[date_column_to_use], errors='coerce').dt.date
                                filtered_kedatangan_df = filtered_kedatangan_df.dropna(subset=['date'])
                                
                                if not filtered_kedatangan_df.empty:
                                    filtered_kedatangan_df[quantity_col] = pd.to_numeric(filtered_kedatangan_df[quantity_col], errors='coerce').fillna(0)
                                    daily_kedatangan = filtered_kedatangan_df.groupby('date')[quantity_col].sum().reset_index()
                                    daily_kedatangan = daily_kedatangan.sort_values('date')
                                    
                                    for _, row in daily_kedatangan.iterrows():
                                        date_str = row['date'].strftime('%d/%m') if hasattr(row['date'], 'strftime') else str(row['date'])
                                        kedatangan_data[date_str] = int(row[quantity_col])
            except:
                pass
            
            # Create kedatangan chart
            target_dates = ["02/06", "03/06", "04/06", "05/06", "06/06", "07/06", "08/06"]
            kedatangan_quantities = [kedatangan_data.get(date, 0) for date in target_dates]
            
            # Create bar chart using plotly
            fig = px.bar(
                y=kedatangan_quantities,
                x=target_dates,
                orientation='v',
                labels={'y': 'Jumlah (ekor)', 'x': 'Tanggal'},
                title='Kedatangan Harian (Berdasarkan Filter)'
            )
            
            # Update layout for better visualization
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=40, b=20),
                showlegend=False
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Display order cards
            if not filtered_data.empty:
                st.markdown("### Daftar Pesanan")
                
                # Sort by completion rate (DESCENDING) to show highest progress first
                filtered_data = filtered_data.sort_values(['completion_rate'], 
                                                        ascending=[False])
                
                # Group display by vendor for better organization
                if selected_supplier == 'Semua':
                    # Show vendor summary cards when viewing all suppliers
                    vendors = filtered_data['supplier'].unique()
                    
                    # Sort vendors by their overall completion rate (DESCENDING)
                    vendor_completion_rates = []
                    for vendor in vendors:
                        vendor_data = filtered_data[filtered_data['supplier'] == vendor]
                        total_ordered = vendor_data['ordered_quantity'].sum()
                        total_delivered = vendor_data['total_delivered'].sum()
                        vendor_completion = (total_delivered / total_ordered * 100) if total_ordered > 0 else 0
                        vendor_completion_rates.append((vendor, vendor_completion))
                    
                    # Sort by completion rate (DESCENDING - highest first)
                    vendor_completion_rates.sort(key=lambda x: x[1], reverse=True)
                    vendors = [vendor for vendor, _ in vendor_completion_rates]
                    
                    for vendor in vendors:
                        vendor_filtered_data = filtered_data[filtered_data['supplier'] == vendor]
                        
                        # Sort vendor's data by completion rate (DESCENDING)
                        vendor_filtered_data = vendor_filtered_data.sort_values(['completion_rate'], ascending=[False])
                        
                        # Show vendor summary card
                        actual_animal_filter = selected_variant if selected_general_animal == "Semua" else selected_general_animal
                        render_vendor_summary_card(
                            vendor, 
                            actual_animal_filter, 
                            vendor_filtered_data, 
                            inbound_df, 
                            selected_general_animal
                        )
                        
                        # Show individual variant cards for this vendor in 2 columns
                        st.markdown(f"#### Detail pesanan {vendor}")
                        
                        # Use 2 columns for variant cards
                        variant_rows = list(vendor_filtered_data.iterrows())
                        for i in range(0, len(variant_rows), 2):
                            col1, col2 = st.columns(2)
                            
                            # First card
                            with col1:
                                _, row = variant_rows[i]
                                render_order_card(
                                    row['supplier'],
                                    row['animal_type'],
                                    row['variant'],
                                    row['ordered_quantity'],
                                    row['total_delivered'],
                                    row['total_outbound'],
                                    row['remaining_quantity'],
                                    row['delivery_count'],
                                    row['completion_rate'],
                                    inbound_df,
                                    selected_general_animal
                                )
                            
                            # Second card (if exists)
                            if i + 1 < len(variant_rows):
                                with col2:
                                    _, row = variant_rows[i + 1]
                                    render_order_card(
                                        row['supplier'],
                                        row['animal_type'],
                                        row['variant'],
                                        row['ordered_quantity'],
                                        row['total_delivered'],
                                        row['total_outbound'],
                                        row['remaining_quantity'],
                                        row['delivery_count'],
                                        row['completion_rate'],
                                        inbound_df,
                                        selected_general_animal
                                    )
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                
                else:
                    # Show individual cards for specific supplier in 2 columns
                    variant_rows = list(filtered_data.iterrows())
                    for i in range(0, len(variant_rows), 2):
                        col1, col2 = st.columns(2)
                        
                        # First card
                        with col1:
                            _, row = variant_rows[i]
                            render_order_card(
                                row['supplier'],
                                row['animal_type'],
                                row['variant'],
                                row['ordered_quantity'],
                                row['total_delivered'],
                                row['total_outbound'],
                                row['remaining_quantity'],
                                row['delivery_count'],
                                row['completion_rate'],
                                inbound_df,
                                selected_general_animal
                            )
                        
                        # Second card (if exists)
                        if i + 1 < len(variant_rows):
                            with col2:
                                _, row = variant_rows[i + 1]
                                render_order_card(
                                    row['supplier'],
                                    row['animal_type'],
                                    row['variant'],
                                    row['ordered_quantity'],
                                    row['total_delivered'],
                                    row['total_outbound'],
                                    row['remaining_quantity'],
                                    row['delivery_count'],
                                    row['completion_rate'],
                                    inbound_df,
                                    selected_general_animal
                                )
            
            else:
                st.info("Tidak ada pesanan yang sesuai dengan filter yang dipilih.")
        
        else:
            st.info("Belum ada data pesanan yang dapat ditampilkan.")
    
    else:
        st.info("Belum ada data masuk yang tercatat. Silakan mulai dengan mencatat hewan masuk.") 