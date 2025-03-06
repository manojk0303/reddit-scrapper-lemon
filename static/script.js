// static/script.js
document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const scrapeButton = document.getElementById('scrapeButton');
    const statusMessage = document.getElementById('statusMessage');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultsCard = document.getElementById('resultsCard');
    const resultCount = document.getElementById('resultCount');
    const resultsBody = document.getElementById('resultsBody');
    const sheetLink = document.getElementById('sheetLink');
    
    // Status check interval (in milliseconds)
    const statusCheckInterval = 2000;
    let statusChecker;
    
    // Function to start scraping
    function startScraping() {
        // Disable button and show loading
        scrapeButton.disabled = true;
        statusMessage.textContent = 'Starting scraping process...';
        statusMessage.className = '';
        loadingSpinner.classList.remove('hidden');
        
        // Make API call to start scraping
        fetch('/start_scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                statusMessage.textContent = 'Scraping in progress...';
                // Start checking status periodically
                statusChecker = setInterval(checkStatus, statusCheckInterval);
            } else {
                showError(data.message || 'Failed to start scraping process');
            }
        })
        .catch(error => {
            showError('Error: ' + error.message);
        });
    }
    
    // Function to check scraping status
    function checkStatus() {
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                // Update status message
                if (data.is_scraping) {
                    statusMessage.textContent = `Scraping in progress... Found ${data.result_count} results so far`;
                } else {
                    // Scraping is complete
                    clearInterval(statusChecker);
                    scrapeButton.disabled = false;
                    loadingSpinner.classList.add('hidden');
                    statusMessage.textContent = `Scraping complete! Found ${data.result_count} results`;
                    statusMessage.className = 'status-success';
                    
                    // Show results if there are any
                    if (data.result_count > 0) {
                        showResults(data.results, data.result_count);
                    }
                }
            })
            .catch(error => {
                clearInterval(statusChecker);
                showError('Error checking status: ' + error.message);
            });
    }
    
    // Function to show error
    function showError(message) {
        statusMessage.textContent = message;
        statusMessage.className = 'status-error';
        scrapeButton.disabled = false;
        loadingSpinner.classList.add('hidden');
        clearInterval(statusChecker);
    }
    
    // Function to display results
    function showResults(results, count) {
        // Update the result count
        resultCount.textContent = `${count} results found`;
        
        // Clear previous results
        resultsBody.innerHTML = '';
        
        // Add new results
        results.forEach(row => {
            const tr = document.createElement('tr');
            
            // Create cells for each column
            // [title, content, url, source, date, keyword]
            [0, 1, 2, 3, 4, 5].forEach(index => {
                const td = document.createElement('td');
                
                // Create clickable links for URLs
                if (index === 2) {
                    const a = document.createElement('a');
                    a.href = row[index];
                    a.textContent = 'View Post';
                    a.target = '_blank';
                    td.appendChild(a);
                } else {
                    // Truncate long text
                    let text = row[index];
                    if (index === 1 && text.length > 100) {
                        text = text.substring(0, 100) + '...';
                    }
                    td.textContent = text;
                }
                
                tr.appendChild(td);
            });
            
            resultsBody.appendChild(tr);
        });
        
        // Show the results card
        resultsCard.classList.remove('hidden');
        
        // Try to extract the spreadsheet ID from the results
        // This assumes that your google sheet URL is stored or can be derived from the results
        // If not, you'll need to modify this to get the URL from your backend
        fetch('/status')
            .then(response => response.json())
            .then(data => {
                // In a real implementation, you might need to get this URL from your backend
                // Here we just use a placeholder that would be replaced with actual code
                // to extract or request the spreadsheet URL
                const spreadsheetUrl = "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID";
                sheetLink.href = spreadsheetUrl;
            });
    }
    
    // Event listeners
    scrapeButton.addEventListener('click', startScraping);
});