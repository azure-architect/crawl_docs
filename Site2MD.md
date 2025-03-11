I'll help you create a script that combines the functionality of crawl.py and html2markdown.py into a single script called site_to_markdown.py. This new script will be able to crawl a website, download its pages, and convert them to markdown format.

Here's the implementation for site_to_markdown.py:

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
    
    print(f"Will download from: {args.url}")
    print(f"HTML files will be saved to: {args.html_dir}")
    if not args.html_only:
        print(f"Markdown files will be saved to: {args.md_dir}")
    
    # Start the crawling and conversion process
    crawl_site(args.url, args.html_dir, args.md_dir, max_pages=args.max_pages, convert=not args.html_only, delay=args.delay)

if __name__ == "__main__":
    main()
```

This script combines the functionality of both crawl.py and html2markdown.py into a single unified tool with the following features:

1. Command-line interface using argparse to accept URL and other options
2. Downloads HTML pages from a specified URL
3. Converts the downloaded HTML to Markdown
4. Customizable options:
   - Specify output directories for HTML and Markdown files
   - Set maximum number of pages to download
   - Adjust delay between requests to be respectful of servers
   - Option to download HTML only without converting to Markdown

To use the script:

1. Save the code to a file named `site_to_markdown.py`
2. Run it from the command line with a URL:
```
python site_to_markdown.py https://example.com
```

Example with options:
```
python site_to_markdown.py https://docs.crewai.com/ --max-pages 100 --html-dir crewai_docs --md-dir crewai_md --delay 2.0
```

The script requires the following packages from your requirements.txt:
- beautifulsoup4
- requests
- html2text

Would you like me to explain any specific part of the script in more detail?
