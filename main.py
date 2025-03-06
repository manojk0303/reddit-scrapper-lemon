# main.py
import asyncio
import yaml
from Scrapers.reddit_scraper import RedditScraper
from Scrapers.twitter_scraper import TwitterScraper
import datetime
import time

async def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    
    reddit_scraper = RedditScraper()
    all_results = []
    
    try:
        # Initialize the Reddit client
        await reddit_scraper.initialize()
        
        for keyword in config["search_keywords"]:
            results = await reddit_scraper.scrape(keyword)
            all_results.extend(results)
            
        # Process Twitter data if needed
        # twitter_scraper = TwitterScraper()
        # for keyword in config["search_keywords"]:
        #     twitter_results = twitter_scraper.scrape(keyword, config["twitter_search_params"])
        #     all_results.extend(twitter_results)
        
        # Save all results to the Google Sheet
        if all_results:
            print(f"Preparing to update sheet with {len(all_results)} rows...")
            
            # Get spreadsheet URL before any operations
            spreadsheet_url = reddit_scraper.get_spreadsheet_url()
            
            # Insert data at the top (after header if exists)
            insertion_row = 2  # Assuming row 1 is header
            
            # Insert in batches to avoid API limits
            batch_size = 100
            for i in range(0, len(all_results), batch_size):
                batch = all_results[i:i + batch_size]
                reddit_scraper.insert_rows(batch, insertion_row)
                print(f"Inserted batch of {len(batch)} rows")
                time.sleep(1)  # Small delay to avoid rate limiting
            
            print(f"Successfully saved {len(all_results)} new results to Google Sheet")
            print(f"Spreadsheet URL: {spreadsheet_url}")
    
    finally:
        # Ensure the Reddit client is properly closed
        await reddit_scraper.close()

if __name__ == "__main__":
    asyncio.run(main())
