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
INBOUND_RANGE = config.get_sheet_range("inbound")
ANIMAL_TYPES = config.get_animal_types()
SHEEP_CATEGORIES = config.get_sheep_categories()
COW_CATEGORIES = config.get_cow_categories()
SHEEP_VENDORS = config.get_sheep_vendors()
COW_VENDORS = config.get_cow_vendors()
HARI_OPTIONS = config.get_hari_options("inbound")
HARI_H = config.get_hari_h_date("inbound")

# Get form labels
form_labels = config.get_form_labels("inbound")

st.header(form_labels["title"])

# Initialize helper
helper = init_helper()

# Initialize session state for animal entries if not exists
if 'animal_entries' not in st.session_state:
    st.session_state.animal_entries = []

# Animal type selection outside the form
animal_type = st.selectbox(
    "Jenis Hewan",
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
            st.markdown(f"##### {form_labels['sections']['domba']}")
            supplier = st.selectbox(
                form_labels["fields"]["vendor_domba"], 
                SHEEP_VENDORS, 
                key="domba_supplier",
                help="Pilih vendor domba"
            )
            variant = st.selectbox(
                form_labels["fields"]["kategori_domba"], 
                SHEEP_CATEGORIES, 
                key="domba_variant",
                help="Pilih kategori dan berat domba"
            )
        else:  # Sapi
            st.markdown(f"##### {form_labels['sections']['sapi']}")
            supplier = st.selectbox(
                form_labels["fields"]["vendor_sapi"], 
                COW_VENDORS, 
                key="sapi_supplier",
                help="Pilih vendor sapi"
            )
            variant = st.selectbox(
                form_labels["fields"]["kategori_sapi"], 
                COW_CATEGORIES, 
                key="sapi_variant",
                help="Pilih kategori dan berat sapi"
            )
    
    with col2:
        st.markdown("##### Jumlah")
        quantity = st.number_input(
            f"Jumlah {animal_type}", 
            min_value=1, 
            value=1, 
            key="quantity",
            help=f"Masukkan jumlah {animal_type.lower()} yang masuk"
        )
    
    # Add entry button with dynamic label
    add_entry = st.form_submit_button(f"Tambah {animal_type}")
    if add_entry:
        # Add new entry using the current form values
        st.session_state.animal_entries.append({
            'animal_type': animal_type,
            'supplier': supplier,
            'variant': variant,
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
                col1.write(f"**Vendor:** {entry['supplier']}")
                col2.write(f"**Kategori:** {entry['variant']}")
                col3.write(f"**Jumlah:** {entry['quantity']}")
                
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
                col1.write(f"**Vendor:** {entry['supplier']}")
                col2.write(f"**Kategori:** {entry['variant']}")
                col3.write(f"**Jumlah:** {entry['quantity']}")
                
                # Delete entry form
                with col4:
                    delete_key = f"delete_sapi_{idx}"
                    if st.button("❌", key=delete_key, help="Hapus entry ini"):
                        st.session_state.animal_entries.remove(entry)
                        st.rerun()

# Main form for final submission
with st.form("main_form"):
    st.subheader("Informasi Nota")
    col1, col2 = st.columns(2)
    
    with col1:
        nomor_nota = st.text_input(form_labels["fields"]["nomor_nota"], key="nomor_nota")
        nama_pengirim = st.text_input(form_labels["fields"]["nama_pengirim"], key="pengirim")
        nama_penerima = st.text_input(form_labels["fields"]["nama_penerima"], key="penerima")
        
        hari_masuk_label = st.selectbox(
            form_labels["fields"]["hari_masuk"],
            list(HARI_OPTIONS.keys()),
            key="hari_masuk_label",
            help=f"Hari H adalah {HARI_H.strftime('%d %B %Y')}"
        )
        tanggal_masuk = HARI_OPTIONS[hari_masuk_label]

    with col2:
        sohibul_qurban = st.text_input(form_labels["fields"]["sohibul_qurban"], key="sohibul")
        catatan = st.text_area(
            form_labels["fields"]["catatan"],
            key="catatan",
            placeholder=form_labels["placeholders"]["catatan"]
        )
        receipt_file = st.file_uploader("Upload Foto Nota", type=['pdf', 'png', 'jpg', 'jpeg'])

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
                st.write(f"Debug: INBOUND_RANGE = {INBOUND_RANGE}")
                st.write(f"Debug: Number of animal entries = {len(st.session_state.animal_entries)}")
            
            # Upload receipt if provided
            receipt_url = None
            if receipt_file is not None:
                # Extract file extension from original filename
                original_filename = receipt_file.name
                file_extension = original_filename.split('.')[-1] if '.' in original_filename else 'jpg'
                
                # Use receipt number for filename, fallback to timestamp if no receipt number
                if nomor_nota.strip():
                    new_filename = f"{nomor_nota.strip()}.{file_extension}"
                else:
                    # Fallback to timestamp if no receipt number provided
                    wib_timezone = pytz.timezone('Asia/Jakarta')
                    file_timestamp = datetime.now(wib_timezone).strftime('%Y%m%d_%H%M%S')
                    new_filename = f"nota_masuk_{file_timestamp}.{file_extension}"
                
                receipt_url = helper.upload_file(
                    receipt_file,
                    new_filename,
                    DRIVE_FOLDER_ID
                )
                if debug_mode:
                    st.write(f"Debug: Receipt uploaded as '{new_filename}' to {receipt_url}")
            
            # Create records for each animal entry
            # Use West Indonesia Time (UTC+7)
            wib_timezone = pytz.timezone('Asia/Jakarta')
            timestamp = datetime.now(wib_timezone).strftime("%Y-%m-%d %H:%M:%S")  # e.g., "03 June 2025 10:00:30"
            
            for idx, entry in enumerate(st.session_state.animal_entries):
                record = [
                    timestamp,                    # Timestamp
                    nomor_nota,                   # Nomor Nota
                    entry['animal_type'],         # Jenis Hewan
                    entry['supplier'],            # Vendor
                    entry['variant'],             # Kategori
                    entry['quantity'],            # Jumlah
                    sohibul_qurban,              # Nama Sohibul Qurban
                    nama_pengirim,               # Nama Pengirim
                    nama_penerima,               # Nama Penerima
                    receipt_url or "",           # Foto Nota
                    tanggal_masuk.strftime("%Y-%m-%d"),  # Tanggal Masuk
                    catatan or ""                # Catatan
                ]
                
                if debug_mode:
                    st.write(f"Debug: Attempting to append record {idx + 1}: {record[:3]}...")
                
                # Append each record to the sheet
                result = helper.append_record(SPREADSHEET_ID, INBOUND_RANGE, record)
                
                if debug_mode:
                    st.write(f"Debug: Append result for record {idx + 1}: {result}")
            
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