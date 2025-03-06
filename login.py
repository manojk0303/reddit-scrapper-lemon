# Step 1: Create a Google Cloud Project and Enable APIs
# ------------------------------------------------------

'''
1. Go to https://console.cloud.google.com/
2. Create a new project (or use an existing one)
3. Enable the following APIs:
   - Google Sheets API
   - Google Drive API

# Step 2: Create Service Account Credentials
# ------------------------------------------

1. In the Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
2. Click "Create Service Account"
3. Enter a name for your service account (e.g., "lemon-sheets-access")
4. Grant this service account the following roles:
   - Project > Editor
5. Click "Continue" and then "Done"
6. Click on the newly created service account
7. Go to the "Keys" tab
8. Click "Add Key" > "Create new key"
9. Choose JSON format
10. The credentials file will be downloaded automatically
11. Rename the file to "credentials.json" and place it in your project directory
'''

# Step 3: Share Your Spreadsheet with the Service Account
# -------------------------------------------------------

'''
1. Open the credentials.json file
2. Find the "client_email" field (looks like: service-account-name@project-id.iam.gserviceaccount.com)
3. Copy this email address
4. Open your Google Sheet
5. Click the "Share" button in the top right
6. Paste the service account email address
7. Set permission to "Editor"
8. Uncheck "Notify people"
9. Click "Share"

Now your service account has access to the spreadsheet.
'''

# Step 4: Use the Modified Script Below
# -------------------------------------

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import SpreadsheetNotFound
import json
import os

def get_or_create_spreadsheet(spreadsheet_name):
    # Define the scope for Google Sheets and Drive APIs
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Check if credentials.json exists
    if not os.path.exists("credentials.json"):
        print("Error: credentials.json file not found in the current directory.")
        return None
    
    # Print email from credentials for debugging
    try:
        with open("credentials.json", "r") as f:
            creds_data = json.load(f)
            service_account_email = creds_data.get("client_email")
            print(f"Using service account: {service_account_email}")
            print("Make sure this email has access to your Google Sheet!")
    except Exception as e:
        print(f"Error reading credentials.json: {e}")
    
    try:
        # Load credentials from the credentials.json file
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        
        try:
            # Try to open the spreadsheet
            spreadsheet = client.open(spreadsheet_name)
            print(f"Spreadsheet '{spreadsheet_name}' found.")
            
            # Get the share URL and print it
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            print(f"Spreadsheet URL: {spreadsheet_url}")
            
        except SpreadsheetNotFound:
            # Create a new spreadsheet if it does not exist
            print(f"Spreadsheet '{spreadsheet_name}' not found. Creating a new one.")
            spreadsheet = client.create(spreadsheet_name)
            
            # Get the share URL and print it
            spreadsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}"
            print(f"New spreadsheet created.")
            print(f"Spreadsheet URL: {spreadsheet_url}")
            
            # Share the spreadsheet with your email
            spreadsheet.share('manojkumarcpyk@gmail.com', perm_type='user', role='writer')
            print(f"Shared with: manojkumarcpyk@gmail.com")
            
        # Return the first worksheet of the spreadsheet
        return spreadsheet.sheet1
    
    except Exception as e:
        print(f"Error accessing Google Sheets: {e}")
        return None

# Usage
sheet = get_or_create_spreadsheet("Lemon Leads")
if sheet:
    print("Accessing sheet:", sheet.title)
    # Test by adding a row
    sheet.append_row(["Test", "This is a test row", "https://example.com", "test source", "2025-03-04", "test keyword"])
    print("Test row added successfully")
else:
    print("Failed to access sheet. Please check the credentials and permissions.")
