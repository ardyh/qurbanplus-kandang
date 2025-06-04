from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pandas as pd
from datetime import datetime
import io
import streamlit as st

# Try to import magic, fallback if not available
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive'
]

class GoogleHelper:
    def __init__(self, credentials_path):
        if credentials_path == "embedded":
            # Use embedded credentials from Streamlit secrets
            creds_info = dict(st.secrets["google_credentials"])
            self.credentials = service_account.Credentials.from_service_account_info(
                creds_info, scopes=SCOPES)
        else:
            # Use traditional file-based credentials
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES)
        
        self.sheets = build('sheets', 'v4', credentials=self.credentials).spreadsheets()
        self.drive = build('drive', 'v3', credentials=self.credentials)

    def append_record(self, spreadsheet_id, range_name, values):
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Parse the range_name to extract sheet name
                if '!' in range_name:
                    sheet_name = range_name.split('!')[0]
                else:
                    sheet_name = range_name
                
                # First, get all existing data to find the next empty row
                try:
                    read_range = f"{sheet_name}!A:A"
                    result = self.sheets.values().get(
                        spreadsheetId=spreadsheet_id,
                        range=read_range
                    ).execute()
                    existing_values = result.get('values', [])
                    next_row = len(existing_values) + 1
                except:
                    # If sheet doesn't exist or has no data, start at row 2 (after header)
                    next_row = 2
                    
                body = {
                    'values': [values]
                }
                
                # Calculate the end column based on number of values
                end_column_index = len(values) - 1
                end_column = chr(65 + end_column_index)  # Convert to letter (A=0, B=1, etc.)
                
                # Create the correct write range
                write_range = f"{sheet_name}!A{next_row}:{end_column}{next_row}"
                
                result = self.sheets.values().update(
                    spreadsheetId=spreadsheet_id,
                    range=write_range,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                return result
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for SSL/network errors
                if "SSL" in error_msg.upper() or "WRONG_VERSION_NUMBER" in error_msg:
                    if attempt < max_retries - 1:
                        st.warning(f"⚠️ Koneksi terputus saat menyimpan (percobaan {attempt + 1}/{max_retries}). Mencoba lagi...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        st.error("🚫 **Gagal menyimpan data - Masalah koneksi**")
                        raise Exception(f"SSL connection failed after {max_retries} attempts: {error_msg}")
                
                # For other errors, retry or raise
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Error menyimpan data (percobaan {attempt + 1}/{max_retries}): {error_msg}")
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception(f"Failed to append record after {max_retries} attempts: {error_msg}")

    def get_records(self, spreadsheet_id, range_name):
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                result = self.sheets.values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
                values = result.get('values', [])
                
                
                if not values:
                    return pd.DataFrame()
                
                # Simplified processing - just pad rows to max length
                max_cols = max(len(row) for row in values) if values else 0
                
                if max_cols == 0:
                    return pd.DataFrame()
                
                # Simple padding without complex filtering
                headers = values[0] + [''] * (max_cols - len(values[0]))
                
                # Pad all data rows to match max_cols
                data_rows = []
                for row in values[1:]:
                    padded_row = row + [''] * (max_cols - len(row))
                    data_rows.append(padded_row)
                
                # Create DataFrame directly
                if data_rows:
                    df = pd.DataFrame(data_rows, columns=headers)
                else:
                    df = pd.DataFrame(columns=headers)
                    
                return df
                
            except Exception as e:
                error_msg = str(e)
                
                # Check for SSL/network errors
                if "SSL" in error_msg.upper() or "WRONG_VERSION_NUMBER" in error_msg:
                    if attempt < max_retries - 1:
                        st.warning(f"⚠️ Koneksi terputus (percobaan {attempt + 1}/{max_retries}). Mencoba lagi dalam {retry_delay} detik...")
                        import time
                        time.sleep(retry_delay)
                        continue
                    else:
                        st.error("🚫 **Masalah Koneksi SSL/Jaringan**")
                        st.error("Kemungkinan penyebab:")
                        st.error("- Koneksi internet tidak stabil")
                        st.error("- Firewall atau proxy memblokir akses")
                        st.error("- Masalah sementara dengan Google API")
                        st.error("**Solusi:** Coba refresh halaman atau cek koneksi internet")
                        return pd.DataFrame()
                
                # For other errors, show general error message
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ Error membaca data (percobaan {attempt + 1}/{max_retries}): {error_msg}")
                    import time
                    time.sleep(retry_delay)
                    continue
                else:
                    st.error(f"❌ Error reading sheet data: {error_msg}")
                    return pd.DataFrame()

    def _detect_mime_type(self, file_bytes, filename):
        """Detect mime type with fallback methods"""
        if MAGIC_AVAILABLE:
            try:
                return magic.from_buffer(file_bytes.getvalue(), mime=True)
            except Exception:
                pass
        
        # Fallback: basic mime type detection based on file extension
        filename_lower = filename.lower()
        if filename_lower.endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif filename_lower.endswith('.png'):
            return 'image/png'
        elif filename_lower.endswith('.pdf'):
            return 'application/pdf'
        elif filename_lower.endswith(('.doc', '.docx')):
            return 'application/msword'
        else:
            return 'application/octet-stream'

    def upload_file(self, file_bytes, filename, folder_id):
        """Upload a file to Google Drive and return the shareable link."""
        try:
            # Detect mime type with fallback
            mime_type = self._detect_mime_type(file_bytes, filename)
            
            # Create file metadata
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }

            # Create media
            media = MediaIoBaseUpload(
                io.BytesIO(file_bytes.getvalue()),
                mimetype=mime_type,
                resumable=True
            )

            # Upload file
            file = self.drive.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()

            return file.get('webViewLink')

        except Exception as e:
            raise Exception(f"Error uploading file to Google Drive: {str(e)}")

def format_record(timestamp, date, animal_type, size, quantity, notes, receipt_url=None):
    record = [
        timestamp,
        date,
        animal_type,
        size,
        quantity,
        notes
    ]
    if receipt_url:
        record.append(receipt_url)
    return record