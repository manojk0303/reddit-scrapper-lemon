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
            self.subreddits = config.get("target_subreddits", [])
            # Filter out empty strings
            self.subreddits = [s for s in self.subreddits if s.strip()]
        except (FileNotFoundError, KeyError):
            # Use environment variables as fallback
            subreddits_env = os.environ.get("TARGET_SUBREDDITS", "")
            self.subreddits = [s.strip() for s in subreddits_env.split(",") if s.strip()]
        
        self.reddit = None
        self.logger.info(f"Initialized with subreddits: {self.subreddits}")
        
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
        
        # If no subreddits specified, search all of Reddit
        if not self.subreddits:
            self.logger.info(f"Searching all of Reddit for '{keyword}'")
            
            # Use Reddit's site-wide search - FIX: Wait for the subreddit coroutine to complete
            subreddit = await self.reddit.subreddit("all")
            async for submission in subreddit.search(query=keyword, sort="new", limit=20):
                # Convert UTC timestamp to human-readable date and time
                created_date = datetime.datetime.fromtimestamp(submission.created_utc)
                human_readable_date = created_date.strftime("%Y-%m-%d %H:%M:%S")
                
                # Get the subreddit name
                subreddit_name = submission.subreddit.display_name
                
                results.append([
                    submission.title,
                    submission.selftext[:500] + "..." if len(submission.selftext) > 500 else submission.selftext,
                    submission.url,
                    f"reddit/r/{subreddit_name}",
                    human_readable_date,
                    keyword
                ])
            
            self.logger.info(f"Found {len(results)} results across all of Reddit")
            return results
            
        # Search specific subreddits
        self.logger.info(f"Searching for '{keyword}' in {len(self.subreddits)} subreddits")
        
        for subreddit_name in self.subreddits:
            try:
                # Skip empty subreddit names that might come from splitting empty env vars
                if not subreddit_name.strip():
                    continue
                    
                self.logger.info(f"Searching in r/{subreddit_name}")
                # FIX: Wait for the subreddit coroutine to complete
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
                        human_readable_date,
                        keyword
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