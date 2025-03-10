import requests
import os
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json

def extract_links_from_navigation(nav_html):
    """Extract all documentation page links from the navigation HTML"""
    soup = BeautifulSoup(nav_html, 'html.parser')
    links = []
    
    # Find all <a> tags with href attributes
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        # Only include internal documentation links (not external links like GitHub)
        if not href.startswith('http'):
            links.append(href)
    
    return links

def download_page(url, output_dir):
    """Download a single page and save it to the output directory"""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Convert relative URL to absolute URL
    if not url.startswith('http'):
        url = urljoin('https://docs.crewai.com', url)
    
    # Send a GET request to the URL
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"Downloading: {url}")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse URL path to create a sensible file structure
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        # Create subdirectories as needed
        current_dir = output_dir
        for part in path_parts[:-1]:
            if part:
                current_dir = os.path.join(current_dir, part)
                if not os.path.exists(current_dir):
                    os.makedirs(current_dir)
        
        # Determine filename
        if path_parts and path_parts[-1]:
            filename = f"{path_parts[-1]}.html"
        else:
            filename = "index.html"
        
        # Save the HTML content
        file_path = os.path.join(current_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
            
        print(f"  Saved to: {file_path}")
        return response.text
        
    except requests.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def download_all_docs(nav_html, output_dir="crewai_docs"):
    """Download all documentation pages based on the navigation menu"""
    links = extract_links_from_navigation(nav_html)
    
    # Add the index page if not already in the list
    if "/" not in links and "" not in links:
        links.insert(0, "/")
    
    print(f"Found {len(links)} pages to download")
    
    # Save the list of links for reference
    with open(os.path.join(output_dir, "page_list.json"), 'w') as f:
        json.dump(links, f, indent=2)
    
    # Download each page
    for i, link in enumerate(links):
        print(f"[{i+1}/{len(links)}] Processing link: {link}")
        download_page(link, output_dir)
        
        # Sleep briefly to avoid hammering the server
        time.sleep(1)
    
    print(f"Download completed. All {len(links)} pages have been saved to {output_dir}")

if __name__ == "__main__":
    # Paste your navigation HTML in a file called nav.html
    # or replace this with the direct HTML string
    nav_html = """<div id="navigation-items">..."""  # Replace with your navigation HTML
    
    # Or load from a file
    # with open('nav.html', 'r', encoding='utf-8') as f:
    #     nav_html = f.read()
    
    download_all_docs(nav_html)
    