import streamlit as st
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

# Show debug mode indicator
if debug_mode:
    st.warning("🧪 Running in DEBUG mode")

# Get sheet ranges from config
INBOUND_RANGE = config.get_sheet_name("inbound")
OUTBOUND_RANGE = config.get_sheet_name("outbound")

st.header("Dashboard Manajemen Qurban")

# Initialize helper
helper = init_helper()

# Load data
inbound_df = helper.get_records(SPREADSHEET_ID, INBOUND_RANGE)
outbound_df = helper.get_records(SPREADSHEET_ID, OUTBOUND_RANGE)

# Process data for goats and cows separately
def process_animal_data(df, animal_type):
    if df.empty:
        return 0
    
    if animal_type == "Domba/Kambing":
        qty_column = "Jumlah Domba/Kambing"
    else:  # Sapi
        qty_column = "Jumlah Sapi"
        
    animal_df = df[df["Hewan"] == animal_type]
    if animal_df.empty:
        return 0
        
    return pd.to_numeric(animal_df[qty_column], errors='coerce').sum()

# Calculate totals
if not inbound_df.empty or not outbound_df.empty:
    st.subheader("Ringkasan Stok")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### Domba/Kambing")
        goats_in = process_animal_data(inbound_df, "Domba/Kambing")
        goats_out = process_animal_data(outbound_df, "Domba/Kambing")
        goats_stock = goats_in - goats_out
        
        st.metric("Total Masuk", f"{int(goats_in)} ekor")
        st.metric("Total Keluar", f"{int(goats_out)} ekor")
        st.metric("Stok Saat Ini", f"{int(goats_stock)} ekor")
        
    with col2:
        st.markdown("##### Sapi")
        cows_in = process_animal_data(inbound_df, "Sapi")
        cows_out = process_animal_data(outbound_df, "Sapi")
        cows_stock = cows_in - cows_out
        
        st.metric("Total Masuk", f"{int(cows_in)} ekor")
        st.metric("Total Keluar", f"{int(cows_out)} ekor")
        st.metric("Stok Saat Ini", f"{int(cows_stock)} ekor")

    # Distribution by type and size
    if not inbound_df.empty:
        st.subheader("Distribusi Hewan")
        
        # Prepare data for goats
        goat_data = inbound_df[inbound_df["Hewan"] == "Domba/Kambing"]
        if not goat_data.empty:
            goat_dist = pd.DataFrame({
                'Tipe': goat_data["Tipe Domba"],
                'Jumlah': pd.to_numeric(goat_data["Jumlah Domba/Kambing"], errors='coerce')
            }).groupby('Tipe').sum().reset_index()
            
            fig_goats = px.bar(
                goat_dist,
                x='Tipe',
                y='Jumlah',
                title='Distribusi Domba/Kambing berdasarkan Ukuran',
                labels={'Tipe': 'Ukuran', 'Jumlah': 'Jumlah (ekor)'}
            )
            st.plotly_chart(fig_goats)
        
        # Prepare data for cows
        cow_data = inbound_df[inbound_df["Hewan"] == "Sapi"]
        if not cow_data.empty:
            cow_dist = pd.DataFrame({
                'Tipe': cow_data["Tipe Sapi"],
                'Jumlah': pd.to_numeric(cow_data["Jumlah Sapi"], errors='coerce')
            }).groupby('Tipe').sum().reset_index()
            
            fig_cows = px.bar(
                cow_dist,
                x='Tipe',
                y='Jumlah',
                title='Distribusi Sapi berdasarkan Ukuran',
                labels={'Tipe': 'Ukuran', 'Jumlah': 'Jumlah (ekor)'}
            )
            st.plotly_chart(fig_cows)

else:
    st.info("Belum ada data yang tercatat. Silakan mulai dengan mencatat hewan masuk.") 