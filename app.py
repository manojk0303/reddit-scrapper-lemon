from flask import Flask, request, jsonify, render_template
import json
import os
from Scrapers.reddit_scraper import RedditScraper
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Reddit API credentials
# Replace with your information
# Use environment variables instead
CLIENT_ID = os.environ.get('REDDIT_CLIENT_ID')
CLIENT_SECRET = os.environ.get('REDDIT_CLIENT_SECRET')
USER_AGENT = os.environ.get('REDDIT_USER_AGENT')

# Initialize scraper
reddit_scraper = RedditScraper(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    user_agent=USER_AGENT
)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle the scraping request from the frontend."""
    try:
        # Get parameters from the request
        data = request.json
        keywords = data.get('keywords', '')
        subreddits = data.get('subreddits', '')
        post_limit = int(data.get('post_limit', 50))
        time_filter = data.get('time_filter', 'month')
        sort_by = data.get('sort_by', 'relevance')
        
        # Validate inputs
        if not keywords and not subreddits:
            return jsonify({'error': 'Please provide at least one keyword or subreddit'}), 400
            
        # Perform scraping
        results = reddit_scraper.scrape_reddit(
            keywords=keywords,
            subreddits=subreddits,
            post_limit=post_limit,
            time_filter=time_filter,
            sort=sort_by
        )
        
        return jsonify({'results': results})
    
    except Exception as e:
        app.logger.error(f"Scraping error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/export', methods=['GET'])
def export_data():
    """API endpoint to export previously scraped data."""
    try:
        # Get most recent results
        results = reddit_scraper.results
        
        if not results:
            return jsonify({
                'status': 'error',
                'message': 'No data available to export',
            }), 404
            
        # Return data for download
        return jsonify({
            'status': 'success',
            'message': f'Exported {len(results)} records',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error exporting data: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)