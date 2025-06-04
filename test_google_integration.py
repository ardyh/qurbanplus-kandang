from sheets_helper import GoogleHelper
import os
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

# Try to load dev.env first, fall back to .env if dev.env doesn't exist
if os.path.exists('dev.env'):
    load_dotenv('dev.env')
    print("Using dev.env configuration")
else:
    load_dotenv('.env')
    print("Using .env configuration")

# Check if we're in test mode
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

def test_google_sheets(helper, spreadsheet_id):
    """Test Google Sheets read and write operations"""
    print("\n=== Testing Google Sheets Integration ===")
    
    # Test data
    test_range = "Inbound!A1:F"
    test_record = [
        datetime.now().strftime("%Y-%m-%d"),
        "Goat",
        "Medium",
        "2",
        "Test entry",
        "https://test-receipt-url.com"
    ]
    
    try:
        # Test writing
        print("\nTesting write operation...")
        result = helper.append_record(spreadsheet_id, test_range, test_record)
        print("✓ Successfully wrote test record")
        
        # Test reading
        print("\nTesting read operation...")
        df = helper.get_records(spreadsheet_id, test_range)
        print("✓ Successfully read records")
        print("\nLast 5 records in sheet:")
        print(df.tail())
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_google_drive(helper, folder_id):
    """Test Google Drive file upload operations"""
    print("\n=== Testing Google Drive Integration ===")
    
    # Ensure tests directory exists
    os.makedirs('tests', exist_ok=True)
    
    # Create a test file
    test_file_path = "tests/test_receipt.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test receipt file")
    
    try:
        # Test file upload
        print("\nTesting file upload...")
        with open(test_file_path, "rb") as f:
            file_content = f.read()
            from io import BytesIO
            file_bytes = BytesIO(file_content)
            
            drive_link = helper.upload_file(
                file_bytes,
                "test_receipt.txt",
                folder_id
            )
            print("✓ Successfully uploaded file")
            print(f"File accessible at: {drive_link}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

def main():
    # Get configuration from environment variables
    spreadsheet_id = os.getenv('MASTER_DATA_SHEETS_ID')
    folder_id = os.getenv('FOTO_NOTA_DRIVE_ID')
    credentials_file = os.getenv('GOOGLE_CREDENTIALS_FILE')
    
    if not all([spreadsheet_id, folder_id, credentials_file]):
        print("❌ Error: Missing required environment variables.")
        print("Please make sure all required variables are set in your env file:")
        print("- MASTER_DATA_SHEETS_ID")
        print("- FOTO_NOTA_DRIVE_ID")
        print("- GOOGLE_CREDENTIALS_FILE")
        return
    
    # Show which mode we're running in
    mode = "DEBUG" if os.getenv('DEBUG_MODE') else "PRODUCTION"
    print(f"\n🔧 Running in {mode} mode using {env_file}")
    print(f"Using Spreadsheet ID: {spreadsheet_id}")
    print(f"Using Drive Folder ID: {folder_id}")
    
    # Initialize helper
    try:
        print("\nInitializing Google Helper...")
        helper = GoogleHelper(credentials_file)
        print("✓ Successfully initialized Google Helper")
    except Exception as e:
        print(f"❌ Error initializing helper: {str(e)}")
        return
    
    # Run tests
    test_google_sheets(helper, spreadsheet_id)
    test_google_drive(helper, folder_id)

if __name__ == "__main__":
    main() 