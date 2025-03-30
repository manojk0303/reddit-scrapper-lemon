# base_scraper.py
import time
import requests
from bs4 import BeautifulSoup
import logging

class BaseScraper:
    """Base class for web scrapers with common functionality."""
    
    def __init__(self, headers=None):
        """
        Initialize the scraper with request headers.
        
        Args:
            headers (dict): Optional request headers
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('scraper')
    
    def make_request(self, url, params=None, retries=3, delay=1):
        """
        Make an HTTP request with retries.
        
        Args:
            url (str): The URL to request
            params (dict): Optional query parameters
            retries (int): Number of retries on failure
            delay (float): Delay between retries in seconds
            
        Returns:
            requests.Response: The response object
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt+1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
                else:
                    self.logger.error(f"Failed to retrieve {url} after {retries} attempts")
                    raise
    
    def parse_html(self, html):
        """
        Parse HTML content with BeautifulSoup.
        
        Args:
            html (str): HTML content
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        return BeautifulSoup(html, 'html.parser')
    
    def extract_text(self, element):
        """
        Safely extract text from a BeautifulSoup element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            str: Extracted text or empty string
        """
        return element.get_text(strip=True) if element else ""
    
    def simple_sentiment_analysis(self, text):
        """
        Perform a simple rule-based sentiment analysis.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            float: Sentiment score (-1.0 to 1.0)
        """
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
