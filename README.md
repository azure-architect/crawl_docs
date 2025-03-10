Here's a combined script that will download HTML from a specified URL and convert it to Markdown in one process:

```python
import requests
import os
import re
import html2text
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import glob
import time
import argparse

def download_page(url, output_dir):
    """Download a single page and save it to the output directory"""
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
        return soup, response.text, filename
        
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None, None, None

def crawl_site(base_url, html_dir, markdown_dir, max_pages=50, convert=True, delay=1):
    """Crawl a website and optionally convert HTML to Markdown"""
    visited = set()
    to_visit = [base_url]
    count = 0
    html_files = []
    
    print(f"Starting to crawl: {base_url}")
    print(f"Will download up to {max_pages} pages")
    
    # Create output directories
    os.makedirs(html_dir, exist_ok=True)
    if convert:
        os.makedirs(markdown_dir, exist_ok=True)
    
    while to_visit and count < max_pages:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
            
        # Only process URLs from the same domain
        if urlparse(current_url).netloc != urlparse(base_url).netloc:
            continue
            
        print(f"[{count+1}/{max_pages}] Processing: {current_url}")
        soup, html, html_file = download_page(current_url, html_dir)
        
        if html_file:
            html_files.append(html_file)
            
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
        
        # Pause to be nice to the server
        time.sleep(delay)
    
    print(f"Crawling completed. Downloaded {count} pages.")
    
    # Convert HTML to Markdown if requested
    if convert and html_files:
        convert_to_markdown(html_dir, markdown_dir)

def clean_markdown(markdown_text):
    """Clean up the markdown to improve readability"""
    # Remove multiple blank lines
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    
    # Fix headers with missing space after #
    markdown_text = re.sub(r'(#+)([^#\s])', r'\1 \2', markdown_text)
    
    # Improve list formatting
    markdown_text = re.sub(r'\n\*', '\n* ', markdown_text)
    
    return markdown_text

def convert_to_markdown(html_dir, markdown_dir):
    """Convert all HTML files in a directory to Markdown"""
    # Create HTML to markdown converter
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.bypass_tables = False
    converter.mark_code = True
    converter.default_image_alt = "Image"
    converter.body_width = 0  # Don't wrap text
    
    # Find all HTML files in the directory and subdirectories
    html_files = glob.glob(os.path.join(html_dir, '**', '*.html'), recursive=True)
    
    print(f"\nFound {len(html_files)} HTML files to convert to Markdown")
    
    for i, html_file in enumerate(html_files):
        # Get the relative path to maintain directory structure
        rel_path = os.path.relpath(html_file, html_dir)
        
        # Change extension from .html to .md
        md_path = os.path.splitext(rel_path)[0] + '.md'
        output_path = os.path.join(markdown_dir, md_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Read HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse with BeautifulSoup to extract the main content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove navigation, sidebar, and other non-content elements
            for element in soup.select('nav, .sidebar, .navigation, header, footer, script, style'):
                if element:
                    element.decompose()
            
            # Try to find the main content
            main_content = soup.select_one('main, .main-content, article, .content, #content')
            
            if main_content:
                html_to_convert = str(main_content)
            else:
                # If we can't identify the main content, use the body
                body = soup.find('body')
                if body:
                    html_to_convert = str(body)
                else:
                    html_to_convert = html_content
            
            # Convert to markdown
            markdown = converter.handle(html_to_convert)
            
            # Clean up the markdown
            markdown = clean_markdown(markdown)
            
            # Save markdown file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            print(f"[{i+1}/{len(html_files)}] Converted: {html_file} -> {output_path}")
            
        except Exception as e:
            print(f"Error converting {html_file}: {e}")
    
    print(f"Conversion completed. All files have been saved to {markdown_dir}")

def main():
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Download a website and convert to Markdown')
    parser.add_argument('url', help='The base URL to crawl')
    parser.add_argument('--html-dir', default='html_docs', help='Directory to save HTML files (default: html_docs)')
    parser.add_argument('--md-dir', default='markdown_docs', help='Directory to save Markdown files (default: markdown_docs)')
    parser.add_argument('--max-pages', type=int, default=50, help='Maximum number of pages to download (default: 50)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--html-only', action='store_true', help='Only download HTML, do not convert to Markdown')
    
    args = parser.parse_args()
    
    # Extract domain name from URL for naming directories
    domain = urlparse(args.url).netloc
    site_name = domain.replace('.', '_')
    
    # Set default directory names based on the domain
    html_dir = args.html_dir if args.html_dir == 'html_docs' else args.html_dir
    markdown_dir = args.md_dir if args.md_dir == 'markdown_docs' else args.md_dir
    
    print(f"Will download from: {args.url}")
    print(f"HTML files will be saved to: {html_dir}")
    if not args.html_only:
        print(f"Markdown files will be saved to: {markdown_dir}")
    
    # Start the crawling and conversion process
    crawl_site(args.url, html_dir, markdown_dir, max_pages=args.max_pages, convert=not args.html_only, delay=args.delay)

if __name__ == "__main__":
    main()
```

## How to use the script:

1. Save the script as `site_to_markdown.py`

2. Install the required packages:
   ```bash
   pip install requests beautifulsoup4 html2text
   ```

3. Run the script with a URL:
   ```bash
   python site_to_markdown.py https://docs.crewai.com/
   ```

4. Additional options:
   ```bash
   # Download up to 100 pages
   python site_to_markdown.py https://docs.crewai.com/ --max-pages 100

   # Use custom directories
   python site_to_markdown.py https://docs.crewai.com/ --html-dir crewai_html --md-dir crewai_markdown

   # Download only HTML (skip Markdown conversion)
   python site_to_markdown.py https://docs.crewai.com/ --html-only

   # Increase delay between requests to 2 seconds
   python site_to_markdown.py https://docs.crewai.com/ --delay 2.0
   ```

5. Get help:
   ```bash
   python site_to_markdown.py --help
   ```

This combined script:
- Accepts a URL as a required command-line argument
- Downloads HTML pages from the website
- Automatically converts the HTML to clean Markdown
- Provides options to customize the process
- Shows progress as it works

The script is now much more flexible and can be used with any website, not just CrewAI documentation.