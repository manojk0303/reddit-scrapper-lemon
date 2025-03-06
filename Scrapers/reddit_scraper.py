# Scrapers/reddit_scraper.py
import asyncpraw
import yaml
from .base_scraper import BaseScraper
import datetime
import os

class RedditScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        # Try to load config from file, or use environment variables
        try:
            with open("config.yaml") as f:
                config = yaml.safe_load(f)
            self.subreddits = config["target_subreddits"]
        except (FileNotFoundError, KeyError):
            # Use environment variables as fallback
            self.subreddits = os.environ.get("TARGET_SUBREDDITS", "").split(",")
        
        self.reddit = None
        
    async def initialize(self):
        """Initialize the Reddit client using environment variables if available"""
        self.logger.info("Initializing Reddit client")
        
        # Get credentials from environment variables or use defaults
        client_id = os.environ.get("REDDIT_CLIENT_ID", "X8Pe0HfUI88nK4zBeHHNWw")
        client_secret = os.environ.get("REDDIT_CLIENT_SECRET", "2aKrCwUG4LMgpWq0OUNmMpV33kTK_w")
        user_agent = os.environ.get("REDDIT_USER_AGENT", "LemonMarketingScraper/1.0")
        
        self.reddit = asyncpraw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
    
    async def scrape(self, keyword):
        """Scrape Reddit posts based on the keyword"""
        if not self.reddit:
            await self.initialize()
            
        results = []
        self.logger.info(f"Searching for '{keyword}' in {len(self.subreddits)} subreddits")
        
        for subreddit_name in self.subreddits:
            try:
                # Skip empty subreddit names that might come from splitting empty env vars
                if not subreddit_name.strip():
                    continue
                    
                self.logger.info(f"Searching in r/{subreddit_name}")
                subreddit = await self.reddit.subreddit(subreddit_name)
                
                search_count = 0
                async for submission in subreddit.search(query=keyword, sort="new", limit=10):
                    search_count += 1
                    
                    # Convert UTC timestamp to human-readable date and time
                    created_date = datetime.datetime.fromtimestamp(submission.created_utc)
                    human_readable_date = created_date.strftime("%Y-%m-%d %H:%M:%S")
                    
                    results.append([
                        submission.title,
                        submission.selftext[:500] + "..." if len(submission.selftext) > 500 else submission.selftext,
                        submission.url,
                        f"reddit/r/{subreddit_name}",
                        human_readable_date,  # Human-readable date format
                        keyword  # Add the keyword as an additional column
                    ])
                
                self.logger.info(f"Found {search_count} results in r/{subreddit_name}")
                
            except Exception as e:
                self.logger.error(f"Error searching r/{subreddit_name}: {e}")
                
        self.logger.info(f"Total results found for '{keyword}': {len(results)}")
        return results
    
    async def close(self):
        """Close the Reddit client"""
        if self.reddit:
            self.logger.info("Closing Reddit client")
            await self.reddit.close()