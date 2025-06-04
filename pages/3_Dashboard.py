import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from dotenv import load_dotenv
from sheets_helper import GoogleHelper

# Always load .env first
load_dotenv('.env')
# If DEBUG_MODE is set, load dev.env to override
if os.getenv('DEBUG_MODE') in ['1', 'true', 'True', 'yes', 'YES']:
    load_dotenv('dev.env', override=True)
    debug_mode = True
else:
    debug_mode = False

# Initialize Google helper
@st.cache_resource
def init_helper():
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    return GoogleHelper(credentials_file)

# Configuration from environment variables
SPREADSHEET_ID = os.getenv('MASTER_DATA_SHEETS_ID')

if not SPREADSHEET_ID:
    st.error("Missing required environment variables. Please check your .env or dev.env file.")
    st.error("MASTER_DATA_SHEETS_ID is required")
    st.stop()

# Show debug mode indicator
if debug_mode:
    st.warning("🧪 Running in DEBUG mode (dev.env overrides)")

# Sheet ranges
INBOUND_RANGE = "Inbound!A1:N"
OUTBOUND_RANGE = "Outbound!A1:N"

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