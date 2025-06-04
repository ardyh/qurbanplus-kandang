import streamlit as st
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
from sheets_helper import GoogleHelper
from config_helper import ConfigHelper
import time

# Always load .env first
load_dotenv('.env')
# If DEBUG_MODE is set, load dev.env to override
if os.getenv('DEBUG_MODE') in ['1', 'true', 'True', 'yes', 'YES']:
    load_dotenv('dev.env', override=True)
    debug_mode = True
else:
    debug_mode = False

# Initialize configuration helper
@st.cache_resource
def init_config():
    return ConfigHelper()

# Initialize Google helper
@st.cache_resource
def init_helper():
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    return GoogleHelper(credentials_file)

# Configuration from environment variables
SPREADSHEET_ID = os.getenv('MASTER_DATA_SHEETS_ID')
DRIVE_FOLDER_ID = os.getenv('FOTO_NOTA_DRIVE_ID')

if not SPREADSHEET_ID or not DRIVE_FOLDER_ID:
    st.error("Missing required environment variables. Please check your .env or dev.env file.")
    st.error("MASTER_DATA_SHEETS_ID and FOTO_NOTA_DRIVE_ID are required")
    st.stop()

# Show debug mode indicator
if debug_mode:
    st.warning("🧪 Running in DEBUG mode (dev.env overrides)")

# Initialize configuration and get values
config = init_config()

# Load configurations from JSON files
OUTBOUND_RANGE = config.get_sheet_name("outbound")
ANIMAL_TYPES = config.get_animal_types()
SHEEP_CATEGORIES = config.get_sheep_categories()
COW_CATEGORIES = config.get_cow_categories()
SHEEP_VENDORS = config.get_sheep_vendors()
COW_VENDORS = config.get_cow_vendors()
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

# Initialize session state for form inputs if not exists
if 'form_input' not in st.session_state:
    st.session_state.form_input = {
        'animal_type': ANIMAL_TYPES[0]
    }

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
            help=f"Masukkan jumlah {animal_type.lower()} yang keluar"
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
        
        hari_keluar_label = st.selectbox(
            form_labels["fields"]["hari_keluar"],
            list(HARI_OPTIONS.keys()),
            key="hari_keluar_label",
            help=f"Hari H adalah {HARI_H.strftime('%d %B %Y')}"
        )
        tanggal_keluar = HARI_OPTIONS[hari_keluar_label]

    with col2:
        tujuan_pengiriman = st.text_input(form_labels["fields"]["tujuan_pengiriman"], key="tujuan")
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
            # Upload receipt if provided
            receipt_url = None
            if receipt_file is not None:
                receipt_url = helper.upload_file(
                    receipt_file,
                    f"nota_keluar_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{receipt_file.name}",
                    DRIVE_FOLDER_ID
                )
            
            # Create records for each animal entry
            timestamp = datetime.now().strftime("%d %B %Y %H:%M:%S")  # e.g., "03 June 2025 10:00:30"
            
            for entry in st.session_state.animal_entries:
                record = [
                    timestamp,                    # Timestamp
                    nomor_nota,                   # Nomor Nota
                    entry['animal_type'],         # Jenis Hewan
                    entry['supplier'],            # Vendor
                    entry['variant'],             # Kategori
                    entry['quantity'],            # Jumlah
                    tujuan_pengiriman,           # Tujuan Pengiriman
                    nama_pengirim,               # Nama Pengirim
                    nama_penerima,               # Nama Penerima
                    receipt_url or "",           # Foto Nota
                    tanggal_keluar.strftime("%Y-%m-%d"),  # Tanggal Keluar
                    catatan or ""                # Catatan
                ]
                
                # Append each record to the sheet
                helper.append_record(SPREADSHEET_ID, OUTBOUND_RANGE, record)
            
            # Clear the form
            st.session_state.animal_entries = []
            
            # Show success popup
            st.toast(config.get_message("success"), icon='✅')
            time.sleep(1)  # Give time for the user to see the message
            st.rerun()
            
        except Exception as e:
            error_msg = str(e)
            st.toast(config.get_message("error"), icon='❌')
            st.exception(e) 