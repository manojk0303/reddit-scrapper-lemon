# app.py
from flask import Flask, render_template, jsonify
import asyncio
import yaml
import os
import sys
import json
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your existing scraper
from Scrapers.reddit_scraper import RedditScraper

app = Flask(__name__)

# Create an event loop for each worker thread
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Global variable to track if scraping is in progress
is_scraping = False
latest_results = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scrape', methods=['POST'])
def start_scrape():
    global is_scraping, latest_results
    
    if is_scraping:
        return jsonify({
            'status': 'error',
            'message': 'A scraping operation is already in progress'
        })
    
    is_scraping = True
    latest_results = []
    
    # Run the scraping process in a background thread
    asyncio.run_coroutine_threadsafe(scrape_and_update(), loop)
    
    return jsonify({
        'status': 'success',
        'message': 'Scraping process started'
    })

@app.route('/status', methods=['GET'])
def get_status():
    global is_scraping, latest_results
    
    return jsonify({
        'is_scraping': is_scraping,
        'result_count': len(latest_results),
        'results': latest_results
    })

async def scrape_and_update():
    global is_scraping, latest_results
    
    try:
        # Load configuration or create it from environment variables if it doesn't exist
        config_path = "config.yaml"
        if not os.path.exists(config_path):
            # Create config from environment variables
            config = {
                "search_keywords": os.environ.get("SEARCH_KEYWORDS", "").split(","),
                "target_subreddits": os.environ.get("TARGET_SUBREDDITS", "").split(",")
            }
        else:
            # Load from file
            with open(config_path) as f:
                config = yaml.safe_load(f)
        
        # Initialize scraper
        reddit_scraper = RedditScraper()
        all_results = []
        
        try:
            # Initialize the Reddit client
            await reddit_scraper.initialize()
            
            for keyword in config["search_keywords"]:
                results = await reddit_scraper.scrape(keyword)
                all_results.extend(results)
                
                # Update latest_results for the status endpoint
                # Convert results to JSON-serializable format
                latest_results = [[str(cell) for cell in row] for row in all_results]
            
            # Save all results to the Google Sheet
            if all_results:
                print(f"Preparing to update sheet with {len(all_results)} rows...")
                
                # Get spreadsheet URL
                spreadsheet_url = reddit_scraper.get_spreadsheet_url()
                
                # Insert data at the top (after header if exists)
                insertion_row = 2  # Assuming row 1 is header
                
                # Insert in batches to avoid API limits
                batch_size = 100
                for i in range(0, len(all_results), batch_size):
                    batch = all_results[i:i + batch_size]
                    reddit_scraper.insert_rows(batch, insertion_row)
                    print(f"Inserted batch of {len(batch)} rows")
                    await asyncio.sleep(1)  # Small delay to avoid rate limiting
                
                print(f"Successfully saved {len(all_results)} new results to Google Sheet")
                print(f"Spreadsheet URL: {spreadsheet_url}")
                
        finally:
            # Ensure the Reddit client is properly closed
            await reddit_scraper.close()
            
    except Exception as e:
        print(f"Error in scraping process: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        is_scraping = False

# Debug helper function to verify templates and static files
def check_paths():
    """Debug function to check that all necessary files exist"""
    print("Current working directory:", os.getcwd())
    print("Templates directory exists:", os.path.exists("templates"))
    print("Template file exists:", os.path.exists("templates/index.html"))
    print("Static directory exists:", os.path.exists("static"))
    print("CSS file exists:", os.path.exists("static/style.css"))
    print("JS file exists:", os.path.exists("static/script.js"))

# Main entry point
if __name__ == "__main__":
    # Check paths for debugging
    check_paths()
    
    # Start the asyncio event loop in a background thread
    import threading
    def run_loop():
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    threading.Thread(target=run_loop, daemon=True).start()
    
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=True)