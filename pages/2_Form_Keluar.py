import streamlit as st
from datetime import datetime, timedelta
import os
from sheets_helper import GoogleHelper
from config_helper import ConfigHelper
from environment_helper import get_environment_helper
import time
import pytz

# Initialize environment helper (cached)
env_helper = get_environment_helper()

# Validate required secrets for current environment
required_secrets = [
    "google.credentials_file",
    "google.spreadsheet_id", 
    "google.drive_folder_id"
]

if not env_helper.validate_required_secrets(required_secrets):
    st.stop()

# Get configuration from environment helper
GOOGLE_CREDENTIALS_FILE = env_helper.get_credentials_file()
SPREADSHEET_ID = env_helper.get_spreadsheet_id()
DRIVE_FOLDER_ID = env_helper.get_drive_folder_id()
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

if not SPREADSHEET_ID or not DRIVE_FOLDER_ID:
    st.error("Missing required configuration. Please check your .streamlit/secrets.toml file.")
    st.error("spreadsheet_id and drive_folder_id are required")
    st.stop()

# Show debug mode indicator
if debug_mode:
    st.warning("🧪 Running in DEBUG mode")

# Initialize configuration and get values
config = init_config()

# Load configurations from JSON files
OUTBOUND_RANGE = config.get_sheet_range("outbound")
ANIMAL_TYPES = config.get_animal_types()
SHEEP_CATEGORIES = config.get_sheep_categories()
COW_CATEGORIES = config.get_cow_categories()
HARI_OPTIONS = config.get_hari_options("outbound")
HARI_H = config.get_hari_h_date("outbound")

# Get form labels
form_labels = config.get_form_labels("outbound")

st.header(form_labels["title"])

# Initialize helper
helper = init_helper()

# Initialize session state for animal entries if not exists
if 'animal_entries' not in st.session_state:
    st.session_state.animal_entries = []

# Animal type selection outside the form
animal_type = st.selectbox(
    form_labels["fields"].get("hewan", "Hewan"),  # Use .get() with fallback
    ANIMAL_TYPES,
    key='animal_type'
)

# Form for adding new entry
with st.form("add_entry_form", clear_on_submit=True):
    st.subheader("Tambah Data Hewan")
    
    # Create two columns for the form
    col1, col2 = st.columns(2)
    
    with col1:
        if animal_type == "Domba/Kambing":
            st.markdown(f"##### {form_labels.get('sections', {}).get('domba', 'Data Domba/Kambing')}")
            tipe_hewan = st.selectbox(
                form_labels["fields"].get("tipe_hewan_domba", "Tipe Hewan (Domba/Kambing)"), 
                SHEEP_CATEGORIES, 
                key="domba_tipe",
                help="Pilih tipe domba/kambing"
            )
        else:  # Sapi
            st.markdown(f"##### {form_labels.get('sections', {}).get('sapi', 'Data Sapi')}")
            tipe_hewan = st.selectbox(
                form_labels["fields"].get("tipe_hewan_sapi", "Tipe Hewan (Sapi)"), 
                COW_CATEGORIES, 
                key="sapi_tipe",
                help="Pilih tipe sapi"
            )
    
    with col2:
        st.markdown("##### Jumlah")
        quantity = st.number_input(
            form_labels["fields"].get("jumlah_hewan", "Jumlah Hewan"), 
            min_value=1, 
            value=1, 
            key="quantity",
            help=f"Masukkan jumlah {animal_type.lower()} yang keluar"
        )
    
    # Add entry button with dynamic label
    add_entry = st.form_submit_button(f"Tambah {animal_type}")
    if add_entry:
        # Add new entry using the current form values
        st.session_state.animal_entries.append({
            'animal_type': animal_type,
            'tipe_hewan': tipe_hewan,
            'quantity': quantity
        })

# Display current entries with better formatting
if st.session_state.animal_entries:
    st.subheader("Data Hewan yang Akan Dicatat")
    
    # Group entries by animal type
    domba_entries = [e for e in st.session_state.animal_entries if e['animal_type'] == "Domba/Kambing"]
    sapi_entries = [e for e in st.session_state.animal_entries if e['animal_type'] == "Sapi"]
    
    # Display Domba entries
    if domba_entries:
        st.markdown("##### Domba/Kambing")
        for idx, entry in enumerate(domba_entries):
            with st.container():
                col1, col2, col3, col4 = st.columns([2,2,1,1])
                col1.write(f"**Tipe:** {entry['tipe_hewan']}")
                col2.write(f"**Jumlah:** {entry['quantity']}")
                
                # Delete entry form
                with col4:
                    delete_key = f"delete_domba_{idx}"
                    if st.button("❌", key=delete_key, help="Hapus entry ini"):
                        st.session_state.animal_entries.remove(entry)
                        st.rerun()
    
    # Display Sapi entries
    if sapi_entries:
        st.markdown("##### Sapi")
        for idx, entry in enumerate(sapi_entries):
            with st.container():
                col1, col2, col3, col4 = st.columns([2,2,1,1])
                col1.write(f"**Tipe:** {entry['tipe_hewan']}")
                col2.write(f"**Jumlah:** {entry['quantity']}")
                
                # Delete entry form
                with col4:
                    delete_key = f"delete_sapi_{idx}"
                    if st.button("❌", key=delete_key, help="Hapus entry ini"):
                        st.session_state.animal_entries.remove(entry)
                        st.rerun()

# Main form for final submission
with st.form("main_form"):
    st.subheader("Informasi Keluar")
    col1, col2 = st.columns(2)
    
    with col1:
        nomor_mobil = st.text_input(
            form_labels["fields"].get("nomor_mobil", "Nomor Mobil (Untuk Kirim Hidup)"), 
            key="nomor_mobil",
            placeholder=form_labels.get("placeholders", {}).get("nomor_mobil", "Masukkan nomor kendaraan untuk pengiriman hidup")
        )
        
        hari_keluar_label = st.selectbox(
            form_labels["fields"].get("hari_keluar", "Hari Keluar"),
            list(HARI_OPTIONS.keys()),
            key="hari_keluar_label",
            help=f"Hari H adalah {HARI_H.strftime('%d %B %Y')}"
        )
        tanggal_keluar = HARI_OPTIONS[hari_keluar_label]
        
        jenis_keluar = st.selectbox(
            form_labels["fields"].get("jenis_keluar", "Jenis Keluar"),
            config.get_form_options("outbound", "jenis_keluar"),
            key="jenis_keluar"
        )
        
        # Show additional input if "Lainnya" is selected
        jenis_keluar_other = ""
        if jenis_keluar == "Lainnya":
            jenis_keluar_other = st.text_input(
                "Sebutkan jenis keluar:",
                key="jenis_keluar_other",
                placeholder=form_labels.get("placeholders", {}).get("jenis_keluar_other", "Sebutkan jenis keluar lainnya")
            )

    with col2:
        surat_jalan = st.text_input(
            form_labels["fields"].get("surat_jalan", "Surat Jalan (Untuk Kirim Hidup)"),
            key="surat_jalan",
            placeholder=form_labels.get("placeholders", {}).get("surat_jalan", "Masukkan nomor/detail surat jalan")
        )
        
        additional_notes = st.text_area(
            form_labels["fields"].get("additional_notes", "Additional Notes"),
            key="additional_notes",
            placeholder=form_labels.get("placeholders", {}).get("additional_notes", "Tambahkan catatan tambahan jika diperlukan")
        )

    submitted = st.form_submit_button("Submit")
    
    if submitted:
        if not st.session_state.animal_entries:
            st.error(config.get_message("validation"))
            st.stop()
            
        try:
            # Debug information only in development
            if debug_mode:
                st.write(f"Debug: Environment = {env_helper.current_env}")
                st.write(f"Debug: SPREADSHEET_ID = {SPREADSHEET_ID}")
                st.write(f"Debug: OUTBOUND_RANGE = {OUTBOUND_RANGE}")
                st.write(f"Debug: Number of animal entries = {len(st.session_state.animal_entries)}")
            
            # Create records for each animal entry
            # Use West Indonesia Time (UTC+7)
            wib_timezone = pytz.timezone('Asia/Jakarta')
            timestamp = datetime.now(wib_timezone).strftime("%Y-%m-%d %H:%M:%S")  # e.g., "03 June 2025 10:00:30"
            
            for entry in st.session_state.animal_entries:
                # Determine final jenis_keluar value
                final_jenis_keluar = jenis_keluar
                if jenis_keluar == "Lainnya" and jenis_keluar_other:
                    final_jenis_keluar = jenis_keluar_other
                
                record = [
                    timestamp,                    # Timestamp
                    entry['animal_type'],         # Hewan
                    entry['tipe_hewan'],          # Tipe Hewan
                    entry['quantity'],            # Jumlah Hewan
                    nomor_mobil or "",           # Nomor Mobil (Untuk Kirim Hidup)
                    tanggal_keluar.strftime("%Y-%m-%d"),  # Hari Keluar
                    final_jenis_keluar,          # Jenis Keluar
                    surat_jalan or "",           # Surat Jalan (Untuk Kirim Hidup)
                    additional_notes or ""        # Additional Notes
                ]
                
                if debug_mode:
                    st.write(f"Debug: Attempting to append record: {record[:3]}...")
                
                # Append each record to the sheet
                result = helper.append_record(SPREADSHEET_ID, OUTBOUND_RANGE, record)
                
                if debug_mode:
                    st.write(f"Debug: Append result: {result}")
            
            # Clear the form
            st.session_state.animal_entries = []
            
            # Show success popup
            success_message = config.get_message("success")
            if env_helper.is_development():
                success_message += " (DEV)"
                
            st.toast(success_message, icon='✅')
            time.sleep(1)  # Give time for the user to see the message
            st.rerun()
            
        except Exception as e:
            if env_helper.is_production():
                # In production, show user-friendly error
                st.toast(config.get_message("error"), icon='❌')
            else:
                # In development, show detailed error with details
                st.toast(f"{config.get_message('error')}: {str(e)}", icon='❌')
                st.exception(e) 