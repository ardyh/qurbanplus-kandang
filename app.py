import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sheets_helper import GoogleHelper
from config_helper import ConfigHelper
from environment_helper import get_environment_helper

# Set page config
st.set_page_config(
    page_title="Master App Tim Kandang",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Show environment info
env_helper.show_environment_info(show_in_sidebar=True)

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

# Title
st.title("Master App Tim Kandang")

if debug_mode:
    st.info("Running in debug mode")

# Initialize helper
helper = init_helper()

# Get configuration values
INBOUND_RANGE = config.get_sheet_name("inbound")
OUTBOUND_RANGE = config.get_sheet_name("outbound")

# Main content
st.markdown("""
### Selamat datang di sistem manajemen kandang Qurban Plus 1446

Sistem ini membantu Anda mengelola:
- 📥 **Data Masuk Hewan** (Form Masuk)
- 📤 **Data Keluar Hewan** (Form Keluar)

Silakan gunakan menu di sidebar untuk navigasi.
""")

# Add statistics if data is available
try:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Statistik Singkat")
        
        # Get latest data from sheets
        inbound_data = helper.get_records(SPREADSHEET_ID, INBOUND_RANGE)
        outbound_data = helper.get_records(SPREADSHEET_ID, OUTBOUND_RANGE)
        
        if not inbound_data.empty:
            st.metric("Total Data Masuk", len(inbound_data))
        else:
            st.metric("Total Data Masuk", 0)
            
        if not outbound_data.empty:
            st.metric("Total Data Keluar", len(outbound_data))
        else:
            st.metric("Total Data Keluar", 0)
            
    with col2:
        st.subheader("🗓️ Informasi Hari H")
        
        # Get Hari H dates from config
        hari_h_inbound = config.get_hari_h_date("inbound")
        hari_h_outbound = config.get_hari_h_date("outbound")
        
        st.info(f"**Hari H Masuk:** {hari_h_inbound.strftime('%d %B %Y')}")
        st.info(f"**Hari H Keluar:** {hari_h_outbound.strftime('%d %B %Y')}")
        
        # Calculate days until Hari H
        today = datetime.now().date()
        days_until_inbound = (hari_h_inbound - today).days
        days_until_outbound = (hari_h_outbound - today).days
        
        if days_until_inbound >= 0:
            st.success(f"Hari H Masuk dalam {days_until_inbound} hari")
        else:
            st.warning(f"Hari H Masuk sudah lewat {abs(days_until_inbound)} hari yang lalu")
            
        if days_until_outbound >= 0:
            st.success(f"Hari H Keluar dalam {days_until_outbound} hari")
        else:
            st.warning(f"Hari H Keluar sudah lewat {abs(days_until_outbound)} hari yang lalu")

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    if debug_mode:
        st.exception(e)

# Footer
st.markdown("---")
st.markdown("© 2024 QurbanPlus 1446 | Tim Kandang") 