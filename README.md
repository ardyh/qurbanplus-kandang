# Farm Management System

A Streamlit-based application for managing animal farm inventory with Google Sheets integration.

## Setup Instructions

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Google Cloud Project:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project
   - Enable both Google Sheets API and Google Drive API for your project
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in service account details and click "Done"
   - Click on the created service account
   - Go to "Keys" tab > "Add Key" > "Create New Key"
   - Choose JSON format and download the credentials file
   - Create a `creds` directory in the project root
   - Place the downloaded credentials file in the `creds` directory

3. Set up Google Sheets:
   - Create a new Google Spreadsheet
   - Create two sheets named exactly "Inbound" and "Outbound"
   - Add the following column headers (A1:F1) in both sheets:
     - Date
     - Animal Type
     - Size
     - Quantity
     - Notes
     - Receipt URL
   - Copy the Spreadsheet ID from the URL (the long string between /d/ and /edit)
   - Update `SPREADSHEET_ID` in app.py with your copied ID
   - Share the spreadsheet with your service account email (with Editor access)

4. Set up Google Drive for Receipts:
   - Go to [Google Drive](https://drive.google.com)
   - Create a new folder for storing receipts
   - Share this folder with your service account email (with Editor access)
   - Open the folder and copy the folder ID from the URL
     (it's the long string after /folders/ in the URL)
   - Update `DRIVE_FOLDER_ID` in app.py with your copied folder ID

5. Run the application:
```bash
streamlit run app.py
```

## Features
- Record incoming animals (goats and cows)
- Record outgoing animals
- Dashboard with overview of farm inventory
- Google Sheets integration for data storage
- Receipt upload functionality with Google Drive integration

## Spreadsheet Structure
Each sheet (Inbound and Outbound) contains the following columns:
- **Date**: Date of the transaction
- **Animal Type**: Type of animal (Goat/Cow)
- **Size**: Size category (Small/Medium/Large)
- **Quantity**: Number of animals
- **Notes**: Additional information
- **Receipt URL**: Google Drive link to uploaded receipt (if any)

## Troubleshooting
- Make sure the service account email has Editor access to both the spreadsheet and Drive folder
- Verify that both Google Sheets API and Google Drive API are enabled in your Google Cloud Project
- Check that the spreadsheet ID and folder ID in app.py match your actual Google resources
- Ensure the sheet names are exactly "Inbound" and "Outbound" (case-sensitive) 