# Scrapers/base_scraper.py
from abc import ABC, abstractmethod
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
from gspread.exceptions import APIError
import os
import json

class BaseScraper(ABC):
    def __init__(self):
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Get Google Sheet name from environment variables or use default
        self.sheet_name = os.environ.get("GOOGLE_SHEET_NAME", "Lemon Leads")
        
        # Connect to Google Sheets
        self.scope = ["https://spreadsheets.google.com/feeds",
                     "https://www.googleapis.com/auth/drive"]
        try:
            # Check if credentials are provided as environment variables
            if "GOOGLE_CREDENTIALS" in os.environ:
                # Create credentials.json from environment variable
                creds_json = os.environ.get("GOOGLE_CREDENTIALS")
                
                # If a file path was provided, load it
                if os.path.exists(creds_json):
                    self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                        creds_json, self.scope)
                else:
                    # Otherwise, try to parse as JSON string
                    try:
                        creds_data = json.loads(creds_json)
                        # Write to a temporary file - needed for ServiceAccountCredentials
                        with open("temp_credentials.json", "w") as f:
                            json.dump(creds_data, f)
                        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                            "temp_credentials.json", self.scope)
                    except json.JSONDecodeError:
                        self.logger.error("Invalid JSON in GOOGLE_CREDENTIALS environment variable")
                        raise
            else:
                # Fall back to credentials.json file
                self.creds = ServiceAccountCredentials.from_json_keyfile_name(
                    "credentials.json", self.scope)
                
            self.client = gspread.authorize(self.creds)
            self.spreadsheet = self.client.open(self.sheet_name)
            self.sheet = self.spreadsheet.sheet1
            self.logger.info("Successfully connected to Google Sheet")
        except Exception as e:
            self.logger.error(f"Error connecting to Google Sheet: {e}")
            raise
    
    @abstractmethod
    async def initialize(self):
        """Initialize any connections or authentication needed for the scraper"""
        pass
    
    @abstractmethod
    async def scrape(self, keyword):
        """Scrape data based on the given keyword"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close any open connections"""
        pass
    
    def get_spreadsheet_url(self):
        """Get the URL of the spreadsheet"""
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet.id}"
    
    def save_to_sheet(self, data):
        """Save a single row of data to the Google Sheet"""
        try:
            self.sheet.append_row(data)
            return True
        except Exception as e:
            self.logger.error(f"Error saving data to sheet: {e}")
            return False
    
    def get_all_data(self):
        """Get all existing data from the sheet"""
        try:
            return self.sheet.get_all_values()
        except Exception as e:
            self.logger.error(f"Error retrieving data from sheet: {e}")
            return []
        
    def insert_rows(self, rows, start_row=2):
        """Insert rows at a specific position in the sheet"""
        try:
            # Insert rows at the specified position
            self.sheet.insert_rows(rows, start_row)
            self.logger.info(f"Inserted {len(rows)} rows at position {start_row}")
            return True
        except gspread.exceptions.APIError as e:
            # Handle token expiration specifically
            if e.response.status_code == 401:  # Unauthorized, likely expired token
                self.logger.info("Refreshing credentials and retrying...")
                self.creds.refresh(None)
                self.client = gspread.authorize(self.creds)
                self.spreadsheet = self.client.open(self.sheet_name)
                self.sheet = self.spreadsheet.sheet1
                # Try again with fresh credentials
                self.sheet.insert_rows(rows, start_row)
                return True
            else:
                raise
        except Exception as e:
            self.logger.error(f"Error inserting rows in sheet: {e}")
            # Print detailed error for debugging
            import traceback
            self.logger.error(traceback.format_exc())
            return False
        
    def clear_sheet(self, preserve_header=True):
        """Clear all data from the sheet"""
        try:
            # Get the dimensions of the sheet
            if preserve_header:
                # Clear everything except the header row
                rows = len(self.sheet.get_all_values())
                if rows > 1:
                    range_name = f"A2:Z{rows}"
                    self.sheet.batch_clear([range_name])
            else:
                # Clear everything
                self.sheet.clear()
            return True
        except Exception as e:
            self.logger.error(f"Error clearing sheet: {e}")
            return False