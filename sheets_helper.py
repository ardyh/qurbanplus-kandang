from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import pandas as pd
from datetime import datetime
import io
import magic
import streamlit as st

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive.file'
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
        # First, get all existing data to find the next empty row
        try:
            result = self.sheets.values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{range_name}!A:A"
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
        
        result = self.sheets.values().update(
            spreadsheetId=spreadsheet_id,
            range=f"{range_name}!A{next_row}:{end_column}{next_row}",  # Specify exact range
            valueInputOption='USER_ENTERED',
            body=body
        ).execute()
        return result

    def get_records(self, spreadsheet_id, range_name):
        result = self.sheets.values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])
        
        if not values:
            return pd.DataFrame()
            
        # Convert to DataFrame with padding for missing columns
        max_cols = max(len(row) for row in values)
        headers = values[0] + [''] * (max_cols - len(values[0]))
        df = pd.DataFrame(values[1:], columns=headers)
        return df

    def upload_file(self, file_bytes, filename, folder_id):
        """Upload a file to Google Drive and return the shareable link."""
        try:
            # Detect mime type
            mime_type = magic.from_buffer(file_bytes.getvalue(), mime=True)
            
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