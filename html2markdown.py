import os
import re
import html2text
from bs4 import BeautifulSoup
import glob

def clean_markdown(markdown_text):
    """Clean up the markdown to improve readability"""
    # Remove multiple blank lines
    markdown_text = re.sub(r'\n{3,}', '\n\n', markdown_text)
    
    # Fix headers with missing space after #
    markdown_text = re.sub(r'(#+)([^#\s])', r'\1 \2', markdown_text)
    
    # Improve list formatting
    markdown_text = re.sub(r'\n\*', '\n* ', markdown_text)
    
    return markdown_text

def convert_html_to_markdown(html_dir, output_dir):
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
    
    print(f"Found {len(html_files)} HTML files to convert")
    
    for html_file in html_files:
        # Get the relative path to maintain directory structure
        rel_path = os.path.relpath(html_file, html_dir)
        
        # Change extension from .html to .md
        md_path = os.path.splitext(rel_path)[0] + '.md'
        output_path = os.path.join(output_dir, md_path)
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        try:
            # Read HTML file
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Parse with BeautifulSoup to extract the main content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove navigation, sidebar, and other non-content elements
            # Adjust these selectors based on the actual HTML structure
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
            
            print(f"Converted: {html_file} -> {output_path}")
            
        except Exception as e:
            print(f"Error converting {html_file}: {e}")
    
    print(f"Conversion completed. All files have been saved to {output_dir}")

if __name__ == "__main__":
    # Directories for HTML files and Markdown output
    html_dir = "crewai_docs"  # Directory with HTML files
    markdown_dir = "crewai_docs_md"  # Where to save Markdown files
    
    convert_html_to_markdown(html_dir, markdown_dir)