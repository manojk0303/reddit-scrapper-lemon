import praw
import time
from datetime import datetime

class RedditScraper:
    """Scraper for Reddit content using official PRAW library."""
    
    def __init__(self, client_id, client_secret, user_agent):
        """Initialize the Reddit scraper with API credentials."""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        self.results = []
        
        # Configure logging
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('scraper')
    
    def scrape_reddit(self, keywords=None, subreddits=None, post_limit=100, time_filter="month", sort="relevance"):
        """
        Scrape Reddit posts based on keywords and subreddits using PRAW.
        
        Args:
            keywords (str): Comma-separated keywords to search for
            subreddits (str): Comma-separated subreddits to search within
            post_limit (int): Maximum number of posts to retrieve per keyword/subreddit
            time_filter (str): Time filter for results (hour, day, week, month, year, all)
            sort (str): Sort method (relevance, hot, new, top, comments)
            
        Returns:
            list: List of scraped posts
        """
        self.results = []
        
        # Parse keywords and subreddits
        keyword_list = [k.strip() for k in keywords.split(',')] if keywords else []
        subreddit_list = [s.strip() for s in subreddits.split(',')] if subreddits else []
        
        # If both keywords and subreddits are provided
        if keyword_list and subreddit_list:
            for subreddit in subreddit_list:
                for keyword in keyword_list:
                    self.logger.info(f"Scraping posts for keyword '{keyword}' in r/{subreddit}")
                    posts = self._search_subreddit(subreddit, keyword, post_limit, time_filter, sort)
                    self.results.extend(posts)
        
        # If only keywords are provided, search all of Reddit
        elif keyword_list:
            for keyword in keyword_list:
                self.logger.info(f"Scraping posts for keyword '{keyword}' across all Reddit")
                posts = self._search_reddit(keyword, post_limit, time_filter, sort)
                self.results.extend(posts)
        
        # If only subreddits are provided, get recent posts from each
        elif subreddit_list:
            for subreddit in subreddit_list:
                self.logger.info(f"Scraping recent posts from r/{subreddit}")
                posts = self._get_subreddit_posts(subreddit, post_limit, time_filter, sort)
                self.results.extend(posts)
        
        return self.results
    
    def _search_reddit(self, query, limit, time_filter, sort):
        """Search all of Reddit for a keyword using PRAW."""
        posts = []
        
        try:
            # Convert sort parameter to PRAW's expected format
            sort_method = self._convert_sort_method(sort)
            
            # Search Reddit
            if sort == "relevance":
                search_results = self.reddit.subreddit("all").search(
                    query, 
                    sort=sort_method, 
                    time_filter=time_filter, 
                    limit=limit
                )
            else:
                search_results = self.reddit.subreddit("all").search(
                    query, 
                    sort=sort_method,
                    time_filter=time_filter,
                    limit=limit
                )
                
            # Extract posts
            for submission in search_results:
                post = self._extract_post_data(submission, keyword=query)
                posts.append(post)
                
        except Exception as e:
            self.logger.error(f"Error searching Reddit: {e}")
            
        return posts
    
    def _search_subreddit(self, subreddit, query, limit, time_filter, sort):
        """Search a specific subreddit for a keyword using PRAW."""
        posts = []
        
        try:
            # Convert sort parameter to PRAW's expected format
            sort_method = self._convert_sort_method(sort)
            
            # Search subreddit
            search_results = self.reddit.subreddit(subreddit).search(
                query, 
                sort=sort_method, 
                time_filter=time_filter, 
                limit=limit
            )
                
            # Extract posts
            for submission in search_results:
                post = self._extract_post_data(submission, keyword=query, subreddit=subreddit)
                posts.append(post)
                
        except Exception as e:
            self.logger.error(f"Error searching subreddit: {e}")
            
        return posts
    
    def _get_subreddit_posts(self, subreddit, limit, time_filter, sort):
        """Get recent posts from a subreddit using PRAW."""
        posts = []
        
        try:
            # Get subreddit
            subreddit_obj = self.reddit.subreddit(subreddit)
            
            # Get posts based on sort method
            if sort == "hot":
                submissions = subreddit_obj.hot(limit=limit)
            elif sort == "new":
                submissions = subreddit_obj.new(limit=limit)
            elif sort == "top":
                submissions = subreddit_obj.top(time_filter=time_filter, limit=limit)
            else:  # Default to hot
                submissions = subreddit_obj.hot(limit=limit)
                
            # Extract posts
            for submission in submissions:
                post = self._extract_post_data(submission, subreddit=subreddit)
                posts.append(post)
                
        except Exception as e:
            self.logger.error(f"Error getting subreddit posts: {e}")
            
        return posts
    
    def _extract_post_data(self, submission, keyword="", subreddit=""):
        """Extract post data from PRAW submission object."""
        # Get content based on post type
        content = ""
        if submission.is_self:
            content = submission.selftext
        else:
            content = submission.url
        
        # Perform sentiment analysis
        title = submission.title
        full_text = f"{title} {content}"
        sentiment = self._simple_sentiment_analysis(full_text)
        
        # Create post object
        post = {
            'title': title,
            'content': content,
            'url': f"https://www.reddit.com{submission.permalink}",
            'subreddit': submission.subreddit.display_name,
            'upvotes': submission.score,
            'comments': submission.num_comments,
            'date': submission.created_utc,
            'keyword': keyword,
            'sentiment': sentiment
        }
        
        return post
    
    def _convert_sort_method(self, sort):
        """Convert sort method to PRAW format."""
        if sort == "relevance":
            return "relevance"
        elif sort == "hot":
            return "hot"
        elif sort == "new":
            return "new"
        elif sort == "top":
            return "top"
        elif sort == "comments":
            return "comments"
        else:
            return "relevance"
    
    def _simple_sentiment_analysis(self, text):
        """Perform a simple rule-based sentiment analysis."""
        if not text:
            return 0.0
            
        # Simple lists of positive and negative words
        positive_words = [
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic',
            'wonderful', 'best', 'love', 'happy', 'helpful', 'useful', 'recommend',
            'positive', 'success', 'successful', 'beneficial', 'effective',
            'impressive', 'innovative', 'outstanding', 'perfect', 'brilliant',
            'excited', 'exciting', 'enjoy', 'enjoyed', 'interesting', 'valuable',
            'favorite', 'thanks', 'thank', 'appreciation', 'appreciate', 'win',
            'winning', 'winner', 'improvement', 'improve', 'improved'
        ]
        
        negative_words = [
            'bad', 'terrible', 'awful', 'horrible', 'poor', 'disappointing',
            'disappointed', 'hate', 'dislike', 'worst', 'waste', 'useless',
            'negative', 'fail', 'failure', 'problem', 'issue', 'trouble',
            'difficult', 'hard', 'complicated', 'confusing', 'confused',
            'annoying', 'annoyed', 'frustrated', 'frustrating', 'sad',
            'unhappy', 'angry', 'broke', 'broken', 'expensive', 'overpriced',
            'avoid', 'avoid', 'sucks', 'suck', 'stupid', 'ridiculous'
        ]
        
        text_lower = text.lower()
        words = text_lower.split()
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Calculate total words (excluding very short words)
        total_words = len([word for word in words if len(word) > 2])
        
        if total_words == 0:
            return 0.0
            
        # Calculate sentiment score
        sentiment_score = (positive_count - negative_count) / (total_words ** 0.5)
        
        # Clamp score between -1 and 1
        return max(min(sentiment_score, 1.0), -1.0)