import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

def download_page(url, output_dir):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Send a GET request to the URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the page title to use as filename
        title = soup.title.string if soup.title else 'index'
        # Clean the title to make it a valid filename
        title = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in title)
        title = title.strip().replace(' ', '_')[:50]  # Limit length
        
        # Save the HTML content
        filename = os.path.join(output_dir, f"{title}.html")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"Downloaded: {url} -> {filename}")
        return soup, response.text
        
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None, None

def crawl_site(base_url, output_dir, max_pages=50):
    visited = set()
    to_visit = [base_url]
    count = 0
    
    while to_visit and count < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
            
        # Only process URLs from the same domain
        if urlparse(current_url).netloc != urlparse(base_url).netloc:
            continue
            
        print(f"Processing: {current_url}")
        soup, html = download_page(current_url, output_dir)
        visited.add(current_url)
        count += 1
        
        if soup:
            # Find all links on the page
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(current_url, href)
                
                # Only add URLs from the same domain and path
                parsed = urlparse(absolute_url)
                base_parsed = urlparse(base_url)
                
                if (parsed.netloc == base_parsed.netloc and 
                    parsed.path.startswith(base_parsed.path) and
                    absolute_url not in visited and
                    '#' not in absolute_url):  # Skip anchor links
                    to_visit.append(absolute_url)
    
    print(f"Crawling completed. Downloaded {count} pages.")

if __name__ == "__main__":
    base_url = "https://docs.crewai.com/"
    output_dir = "crewai_docs"
    
    # Create the output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Start crawling
    crawl_site(base_url, output_dir)