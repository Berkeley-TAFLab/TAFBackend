import os
import requests
import time
from pathlib import Path

# Configuration
API_URL = "http://127.0.0.1:3000"  # Adjust if your server runs on a different host/port
UPLOADS_DIR = "uploads"  # Directory containing CSV files to upload
TARGET_TABLE = "boat_data"  # Table to upload to

def main():
    # Create a Path object for the uploads directory
    uploads_path = Path(UPLOADS_DIR)
    
    # Ensure the uploads directory exists
    if not uploads_path.exists() or not uploads_path.is_dir():
        print(f"Error: Directory '{UPLOADS_DIR}' not found!")
        return
    
    # Get all CSV files in the directory
    csv_files = list(uploads_path.glob("*.csv"))
    
    if not csv_files:
        print(f"No CSV files found in '{UPLOADS_DIR}' directory.")
        return
    
    print(f"Found {len(csv_files)} CSV files to upload.")
    
    # Upload each file
    successful = 0
    failed = 0
    
    for file_path in csv_files:
        filename = file_path.name
        print(f"Uploading {filename}...")
        
        try:
            # Open the file and create a files dict for the POST request
            with open(file_path, 'rb') as file:
                files = {'file': (filename, file, 'text/csv')}
                
                # Send POST request to upload endpoint
                response = requests.post(
                    f"{API_URL}/upload/{TARGET_TABLE}",
                    files=files
                )
                
                # Check response
                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ Success: {filename} uploaded ({result.get('rows', 'N/A')} rows)")
                    successful += 1
                elif response.status_code == 409:
                    print(f"⚠ Skipped: {filename} already exists in the database.")
                    failed += 1
                else:
                    print(f"✗ Failed: {filename} - {response.status_code} - {response.json().get('error', 'Unknown error')}")
                    failed += 1
                
                # Add a small delay to avoid overloading the server
                time.sleep(0.5)
                
        except Exception as e:
            print(f"✗ Error uploading {filename}: {str(e)}")
            failed += 1
    
    # Print summary
    print("\nUpload Summary:")
    print(f"  Total files processed: {len(csv_files)}")
    print(f"  Successfully uploaded: {successful}")
    print(f"  Failed: {failed}")

if __name__ == "__main__":
    main()
