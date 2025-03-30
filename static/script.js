// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const scrapeButton = document.getElementById('scrapeButton');
    const keywordsInput = document.getElementById('keywords');
    const subredditsInput = document.getElementById('subreddits');
    const postLimitInput = document.getElementById('postLimit');
    const timeFilterSelect = document.getElementById('timeFilter');
    const sortBySelect = document.getElementById('sortBy');
    const statusMessage = document.getElementById('statusMessage');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsCard = document.getElementById('resultsCard');
    const resultCount = document.getElementById('resultCount');
    const resultsBody = document.getElementById('resultsBody');
    const searchResults = document.getElementById('searchResults');
    const exportCSVButton = document.getElementById('exportCSV');
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    const insightsContainer = document.getElementById('insightsContainer');
    
    // Store the fetched data
    let scrapedData = [];
    
    // Event listeners
    scrapeButton.addEventListener('click', startScraping);
    searchResults.addEventListener('input', filterResults);
    exportCSVButton.addEventListener('click', exportToCSV);
    
    // Tab navigation
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Remove active class from all buttons and contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            button.classList.add('active');
            document.getElementById(`${tabName}Tab`).classList.add('active');
        });
    });
    
    // Start scraping function
    function startScraping() {
        const keywords = keywordsInput.value.trim();
        const subreddits = subredditsInput.value.trim();
        const postLimit = postLimitInput.value;
        const timeFilter = timeFilterSelect.value;
        const sortBy = sortBySelect.value;
        
        if (!keywords && !subreddits) {
            alert('Please enter at least one keyword or subreddit to scrape');
            return;
        }
        
        // Update UI to show scraping in progress
        scrapeButton.disabled = true;
        statusMessage.textContent = 'Scraping in progress...';
        loadingSpinner.classList.remove('hidden');
        resultsBody.innerHTML = '';
        resultsCard.classList.add('hidden');
        
        // Prepare the data to send
        const data = {
            keywords: keywords,
            subreddits: subreddits,
            post_limit: postLimit,
            time_filter: timeFilter,
            sort_by: sortBy
        };
        
        // Send request to the server
        fetch('/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            scrapedData = data.results;
            displayResults(scrapedData);
            generateInsights(scrapedData);
            displayEngagementAnalysis(scrapedData);
            displaySentimentAnalysis(scrapedData);
            
            statusMessage.textContent = 'Scraping completed successfully!';
            resultsCard.classList.remove('hidden');
            scrapeButton.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            statusMessage.textContent = 'Error: ' + error.message;
            scrapeButton.disabled = false;
        })
        .finally(() => {
            loadingSpinner.classList.add('hidden');
        });
    }
    
    // Display results in the table
    function displayResults(results) {
        resultsBody.innerHTML = '';
        
        if (results.length === 0) {
            resultCount.textContent = 'No results found';
            return;
        }
        
        resultCount.textContent = `${results.length} results found`;
        
        results.forEach(item => {
            const row = document.createElement('tr');
            
            // Truncate content for display
            const truncatedContent = item.content && item.content.length > 150 
                ? item.content.substring(0, 150) + '...' 
                : item.content || 'No content';
                
            // Determine sentiment class
            let sentimentClass = 'sentiment-neutral';
            if (item.sentiment > 0.2) sentimentClass = 'sentiment-positive';
            if (item.sentiment < -0.2) sentimentClass = 'sentiment-negative';
            
            row.innerHTML = `
                <td><a href="${item.url}" target="_blank">${item.title}</a></td>
                <td>${truncatedContent}</td>
                <td>${item.subreddit}</td>
                <td><a href="${item.url}" target="_blank">Link</a></td>
                <td>${item.upvotes}</td>
                <td>${item.comments}</td>
                <td>${new Date(item.date * 1000).toLocaleDateString()}</td>
                <td>${item.keyword}</td>
                <td class="${sentimentClass}">${formatSentiment(item.sentiment)}</td>
            `;
            
            resultsBody.appendChild(row);
        });
    }
    
    // Format sentiment score for display
    function formatSentiment(score) {
        if (score > 0.2) return 'Positive';
        if (score < -0.2) return 'Negative';
        return 'Neutral';
    }
    
    // Filter results based on search query
    function filterResults() {
        const query = searchResults.value.toLowerCase();
        
        if (!query) {
            displayResults(scrapedData);
            return;
        }
        
        const filtered = scrapedData.filter(item => {
            return (
                item.title.toLowerCase().includes(query) ||
                (item.content && item.content.toLowerCase().includes(query)) ||
                item.subreddit.toLowerCase().includes(query) ||
                item.keyword.toLowerCase().includes(query)
            );
        });
        
        displayResults(filtered);
    }
    
    // Generate marketing insights
    function generateInsights(data) {
        insightsContainer.innerHTML = '';
        
        if (data.length === 0) return;
        
        // Top subreddits by engagement
        const subredditStats = {};
        data.forEach(item => {
            if (!subredditStats[item.subreddit]) {
                subredditStats[item.subreddit] = {
                    count: 0,
                    upvotes: 0,
                    comments: 0
                };
            }
            
            subredditStats[item.subreddit].count++;
            subredditStats[item.subreddit].upvotes += item.upvotes;
            subredditStats[item.subreddit].comments += item.comments;
        });
        
        // Sort subreddits by engagement (upvotes + comments)
        const sortedSubreddits = Object.keys(subredditStats).sort((a, b) => {
            const engagementA = subredditStats[a].upvotes + subredditStats[a].comments;
            const engagementB = subredditStats[b].upvotes + subredditStats[b].comments;
            return engagementB - engagementA;
        });
        
        // Top 3 subreddits by engagement
        const topSubreddits = sortedSubreddits.slice(0, 3);
        
        // Calculate overall engagement
        const totalUpvotes = data.reduce((sum, item) => sum + item.upvotes, 0);
        const totalComments = data.reduce((sum, item) => sum + item.comments, 0);
        const avgUpvotes = totalUpvotes / data.length;
        const avgComments = totalComments / data.length;
        
        // Calculate sentiment distribution
        const sentiments = {
            positive: data.filter(item => item.sentiment > 0.2).length,
            neutral: data.filter(item => item.sentiment >= -0.2 && item.sentiment <= 0.2).length,
            negative: data.filter(item => item.sentiment < -0.2).length
        };
        
        // Create insight cards
        const insights = [
            {
                title: 'Total Posts',
                value: data.length,
                description: 'Total number of posts scraped'
            },
            {
                title: 'Total Engagement',
                value: totalUpvotes + totalComments,
                description: 'Sum of upvotes and comments'
            },
            {
                title: 'Avg. Upvotes',
                value: avgUpvotes.toFixed(1),
                description: 'Average upvotes per post'
            },
            {
                title: 'Avg. Comments',
                value: avgComments.toFixed(1),
                description: 'Average comments per post'
            },
            {
                title: 'Top Subreddit',
                value: topSubreddits[0] || 'N/A',
                description: 'Most engaged subreddit'
            },
            {
                title: 'Sentiment',
                value: `${Math.round(sentiments.positive / data.length * 100)}% Pos`,
                description: `${sentiments.negative} negative, ${sentiments.neutral} neutral, ${sentiments.positive} positive`
            }
        ];
        
        // Append insight cards to container
        insights.forEach(insight => {
            const card = document.createElement('div');
            card.className = 'insight-card';
            card.innerHTML = `
                <div class="insight-title">${insight.title}</div>
                <div class="insight-value">${insight.value}</div>
                <div class="insight-description">${insight.description}</div>
            `;
            insightsContainer.appendChild(card);
        });
    }
    
    // Display engagement analysis
    function displayEngagementAnalysis(data) {
        const engagementStats = document.getElementById('engagementStats');
        const engagementChart = document.getElementById('engagementChart');
        
        if (data.length === 0) return;
        
        // Calculate engagement stats by subreddit
        const subredditEngagement = {};
        data.forEach(item => {
            if (!subredditEngagement[item.subreddit]) {
                subredditEngagement[item.subreddit] = {
                    posts: 0,
                    upvotes: 0,
                    comments: 0,
                    upvoteToComment: 0
                };
            }
            
            subredditEngagement[item.subreddit].posts++;
            subredditEngagement[item.subreddit].upvotes += item.upvotes;
            subredditEngagement[item.subreddit].comments += item.comments;
        });
        
        // Calculate upvote to comment ratio
        Object.keys(subredditEngagement).forEach(subreddit => {
            const stats = subredditEngagement[subreddit];
            stats.upvoteToComment = stats.comments > 0 ? stats.upvotes / stats.comments : 0;
        });
        
        // Sort by total engagement
        const sortedSubreddits = Object.keys(subredditEngagement).sort((a, b) => {
            const engagementA = subredditEngagement[a].upvotes + subredditEngagement[a].comments;
            const engagementB = subredditEngagement[b].upvotes + subredditEngagement[b].comments;
            return engagementB - engagementA;
        });
        
        // Display engagement stats
        engagementStats.innerHTML = '<h3>Engagement by Subreddit</h3>';
        const statsList = document.createElement('ul');
        statsList.style.listStyle = 'none';
        statsList.style.padding = '0';
        
        sortedSubreddits.slice(0, 5).forEach(subreddit => {
            const stats = subredditEngagement[subreddit];
            const totalEngagement = stats.upvotes + stats.comments;
            
            const item = document.createElement('li');
            item.style.marginBottom = '10px';
            item.style.padding = '10px';
            item.style.backgroundColor = 'white';
            item.style.borderRadius = '4px';
            
            item.innerHTML = `
                <strong>${subreddit}</strong><br>
                Total Engagement: ${totalEngagement}<br>
                Avg. Upvotes: ${(stats.upvotes / stats.posts).toFixed(1)}<br>
                Avg. Comments: ${(stats.comments / stats.posts).toFixed(1)}<br>
                Upvote/Comment Ratio: ${stats.upvoteToComment.toFixed(1)}
            `;
            
            statsList.appendChild(item);
        });
        
        engagementStats.appendChild(statsList);
        
        // Create placeholder for engagement chart
        engagementChart.innerHTML = '<div style="height: 100%; display: flex; align-items: center; justify-content: center; text-align: center; color: #666;">Engagement chart would be rendered here.<br>Integration with a chart library like Chart.js is recommended.</div>';
    }
    
    // Display sentiment analysis
    function displaySentimentAnalysis(data) {
        const sentimentBreakdown = document.getElementById('sentimentBreakdown');
        const sentimentChart = document.getElementById('sentimentChart');
        
        if (data.length === 0) return;
        
        // Calculate sentiment by subreddit
        const subredditSentiment = {};
        data.forEach(item => {
            if (!subredditSentiment[item.subreddit]) {
                subredditSentiment[item.subreddit] = {
                    posts: 0,
                    totalSentiment: 0,
                    positive: 0,
                    neutral: 0,
                    negative: 0
                };
            }
            
            subredditSentiment[item.subreddit].posts++;
            subredditSentiment[item.subreddit].totalSentiment += item.sentiment;
            
            if (item.sentiment > 0.2) {
                subredditSentiment[item.subreddit].positive++;
            } else if (item.sentiment < -0.2) {
                subredditSentiment[item.subreddit].negative++;
            } else {
                subredditSentiment[item.subreddit].neutral++;
            }
        });
        
        // Calculate average sentiment
        Object.keys(subredditSentiment).forEach(subreddit => {
            const stats = subredditSentiment[subreddit];
            stats.avgSentiment = stats.totalSentiment / stats.posts;
        });
        
        // Sort by average sentiment
        const sortedSubreddits = Object.keys(subredditSentiment).sort((a, b) => {
            return subredditSentiment[b].avgSentiment - subredditSentiment[a].avgSentiment;
        });
        
        // Display sentiment breakdown
        sentimentBreakdown.innerHTML = '<h3>Sentiment by Subreddit</h3>';
        const breakdownList = document.createElement('ul');
        breakdownList.style.listStyle = 'none';
        breakdownList.style.padding = '0';
        
        sortedSubreddits.slice(0, 5).forEach(subreddit => {
            const stats = subredditSentiment[subreddit];
            
            const item = document.createElement('li');
            item.style.marginBottom = '10px';
            item.style.padding = '10px';
            item.style.backgroundColor = 'white';
            item.style.borderRadius = '4px';
            
                
            // Determine sentiment class
            let sentimentClass = 'sentiment-neutral';
            if (stats.avgSentiment > 0.2) {
                sentimentClass = 'sentiment-positive';
            } else if (stats.avgSentiment < -0.2) {
                sentimentClass = 'sentiment-negative';
            }
            item.innerHTML = `
                <strong>${subreddit}</strong><br>
                <span class="${sentimentClass}">Avg. Sentiment: ${stats.avgSentiment.toFixed(2)}</span><br>
                Positive: ${stats.positive} (${Math.round(stats.positive / stats.posts * 100)}%)<br>
                Neutral: ${stats.neutral} (${Math.round(stats.neutral / stats.posts * 100)}%)<br>
                Negative: ${stats.negative} (${Math.round(stats.negative / stats.posts * 100)}%)
            `;
            
            breakdownList.appendChild(item);
        });
        
        sentimentBreakdown.appendChild(breakdownList);
        
        // Create placeholder for sentiment chart
        sentimentChart.innerHTML = '<div style="height: 100%; display: flex; align-items: center; justify-content: center; text-align: center; color: #666;">Sentiment analysis chart would be rendered here.<br>Integration with a chart library like Chart.js is recommended.</div>';
    }
    
    // Export to CSV function
    function exportToCSV() {
        if (scrapedData.length === 0) {
            alert('No data to export');
            return;
        }
        
        // Prepare CSV headers
        const headers = [
            'Title',
            'Content',
            'Subreddit',
            'URL',
            'Upvotes',
            'Comments',
            'Date',
            'Keyword',
            'Sentiment'
        ];
        
        // Prepare CSV rows
        const rows = scrapedData.map(item => {
            return [
                `"${item.title.replace(/"/g, '""')}"`,
                `"${(item.content || '').replace(/"/g, '""')}"`,
                item.subreddit,
                item.url,
                item.upvotes,
                item.comments,
                new Date(item.date * 1000).toLocaleDateString(),
                item.keyword,
                item.sentiment
            ];
        });
        
        // Combine headers and rows
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n');
        
        // Create a blob and download link
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        
        link.setAttribute('href', url);
        link.setAttribute('download', `reddit_data_${new Date().toISOString().split('T')[0]}.csv`);
        link.style.display = 'none';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
});
