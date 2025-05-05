
import requests
from bs4 import BeautifulSoup
import psycopg2
import time
import re
from urllib.parse import urljoin, urlparse, parse_qs


DB_CONFIG = {
    "dbname": "legal_db",
    "user": "legal_user",
    "password": "securepassword",
    "host": "localhost",
    "port": "5432"
}

BASE_URL = "https://app.leg.wa.gov/rcw/"


TITLE_URLS = {
         "1": "https://app.leg.wa.gov/rcw/default.aspx?Cite=1",
    "2": "https://app.leg.wa.gov/rcw/default.aspx?Cite=2",
    "3": "https://app.leg.wa.gov/rcw/default.aspx?Cite=3"
}

# Add headers to prevent being blocked
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
}


def create_db():
    """Create the PostgreSQL database schema."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS legal_records (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            chapter TEXT NOT NULL,
            section TEXT NOT NULL,
            legal_text TEXT NOT NULL,
            citation_link TEXT NOT NULL,
            embedding BYTEA  
        );
    ''')
    
    conn.commit()
    conn.close()
    print("Database initialized successfully.")

def save_to_db(title, chapter, section, text, link):
    """Save law records to SQLite database and print confirmation."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO legal_records (title, chapter, section, legal_text, citation_link) VALUES (%s, %s, %s, %s, %s)",
        (title, chapter, section, text, link)
    )

    conn.commit()
    conn.close()

    print(f"✅ Inserted: {title} | {chapter} | {section} | {link}")

def get_soup(url, retries=3):
    """Make a request with retries and return a BeautifulSoup object."""
    # Check if the URL is for a PDF
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if 'pdf' in query_params and query_params['pdf'][0].lower() == 'true':
        print(f"⚠️ Skipping PDF URL: {url}")
        return None
    
    for attempt in range(retries):
        try:
            print(f"Requesting: {url}")
            res = requests.get(url, headers=HEADERS, timeout=30)
            res.raise_for_status()
            
            # Check content type
            content_type = res.headers.get('Content-Type', '').lower()
            if 'pdf' in content_type or 'application/octet-stream' in content_type:
                print(f"⚠️ Skipping URL with PDF content: {url}")
                return None
                
            # Try to parse as HTML
            try:
                return BeautifulSoup(res.text, "html.parser")
            except Exception as parse_error:
                print(f"⚠️ Failed to parse HTML: {str(parse_error)}")
                return None
                
        except (requests.RequestException, requests.ConnectionError) as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2  # Exponential backoff
                print(f"⚠️ Attempt {attempt+1} failed for {url}. Retrying in {wait_time}s... Error: {str(e)}")
                time.sleep(wait_time)
            else:
                print(f"❌ ERROR: Failed to fetch {url} after {retries} attempts. Error: {str(e)}")
                return None

# def clean_url(url):
#     """Clean URL by removing PDF parameter if present."""
#     parsed_url = urlparse(url)
#     query_params = parse_qs(parsed_url.query)
    
#     # Remove pdf parameter if present
#     if 'pdf' in query_params:
#         del query_params['pdf']
    
#     # Reconstruct the URL without the pdf parameter
#     clean_params = "&".join([f"{k}={v[0]}" for k, v in query_params.items()])
#     clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
#     if clean_params:
#         clean_url += f"?{clean_params}"
    
#     return clean_url

def extract_chapter_links(title_url, title_num):
    """Extract chapter links from a title page."""
    soup = get_soup(title_url)
    if not soup:
        return []
    
    # Debug: Print page title to confirm correct page
    page_title = soup.title.text if soup.title else "No title found"
    print(f"Page title: {page_title}")
    
    chapter_links = []
    
    # Find all links in the main content area
    links = soup.find_all('a', href=True)
    
    # Print all found links for debugging
    print(f"Found {len(links)} links on the page")
    
    # First pattern - look for links with cite parameter matching title.chapter format
    for link in links:
        href = link.get('href', '').lower()
        text = link.text.strip()

        
        # Look for links like "https://app.leg.wa.gov/RCW/default.aspx?cite=2.04"
        if 'rcw/default.aspx?cite=' in href or 'rcw/default.aspx?Cite=' in href:
            cite_match = re.search(r'cite=(\d+\.\d+)', href, re.IGNORECASE)
            if cite_match:
                cite_value = cite_match.group(1)
                title_part = cite_value.split('.')[0]
                
                # Make sure it's a chapter of the current title
                if title_part == title_num:
                    # If the link text doesn't look like a chapter name, try to create one
                    if not text or not re.search(r'chapter|sections', text, re.IGNORECASE):
                        text = f"Chapter {cite_value}"
                    
                    # Clean the URL (remove PDF parameter if present)
                    # cleaned_url = clean_url(href)
                    
                    # Normalize URL
                    chapter_url = f"https://app.leg.wa.gov/RCW/default.aspx?cite={cite_value}"
                    chapter_links.append((text, chapter_url))
                    print(f"Found chapter link: {text} -> {chapter_url}")
    
    # If no links found with first approach, try another method
    if not chapter_links:
        print("Trying alternate chapter link detection method...")
        
        # Try to find any links that might be chapters based on URL pattern and context
        for link in links:
            href = link.get('href', '').lower()
            text = link.text.strip()
            
            # Look for links containing the title number and having a potential chapter format
            if f"cite={title_num}." in href.lower() and re.search(r'\d+\.\d+', href):
                # Clean the URL
                if href.startswith('/'):
                    full_url = "https://app.leg.wa.gov" + href
                else:
                    full_url = href
                
                # Remove PDF parameter if present
                full_url = clean_url(full_url)
                
                # If the text is empty or doesn't look like chapter name, create one
                if not text:
                    # Extract chapter number from the URL
                    chapter_match = re.search(r'cite=(\d+\.\d+)', href, re.IGNORECASE)
                    if chapter_match:
                        text = f"Chapter {chapter_match.group(1)}"
                    else:
                        text = f"Chapter {href.split('=')[-1]}"
                
                chapter_links.append((text, full_url))
                print(f"Found alternate chapter link: {text} -> {full_url}")
    
    return chapter_links

def extract_section_links(chapter_url):
    """Extract section links from a chapter page with URL deduplication."""
    soup = get_soup(chapter_url)
    if not soup:
        return []
    
    # Use a dictionary to track unique URLs
    unique_section_urls = {}
    
    # Extract title.chapter part from URL
    chapter_match = re.search(r'cite=(\d+\.\d+)', chapter_url, re.IGNORECASE)
    if not chapter_match:
        print(f"⚠️ Could not extract chapter pattern from URL: {chapter_url}")
        return []
    
    chapter_prefix = chapter_match.group(1)
    
    # Find all links on the page
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        text = link.text.strip()
        
        # Look for links with section pattern (e.g., 2.04.010)
        section_pattern = f"{chapter_prefix}\.\d+"
        
        # Check URL for section pattern
        if href and re.search(r'cite=\d+\.\d+\.\d+', href, re.IGNORECASE):
            # Clean the URL (remove PDF parameter if present)
            href = clean_url(href)
            
            # Fix the URL if it's a relative path
            if href.startswith('/'):
                full_url = "https://app.leg.wa.gov" + href
            else:
                full_url = href
            
            # Extract section ID from URL for consistent naming
            section_match = re.search(r'cite=(\d+\.\d+\.\d+)', href, re.IGNORECASE)
            if section_match:
                section_id = section_match.group(1)
                
                # Store only unique URLs with their proper section ID
                if full_url not in unique_section_urls:
                    unique_section_urls[full_url] = section_id
                    print(f"Found unique section link: {section_id} -> {full_url}")
    
    # Convert the dictionary to a list of tuples
    section_links = [(section_id, url) for url, section_id in unique_section_urls.items()]
    
    print(f"Found {len(section_links)} unique section links")
    return section_links


def extract_section_content(section_url):
    """Extract the clean section content from a section page."""
    # Clean the URL (remove PDF parameter if present)
    section_url = clean_url(section_url)
    
    soup = get_soup(section_url)
    if not soup:
        return None
    
    result = {}
    
    # Try to find the RCW section number
    rcw_number = None
    rcw_links = soup.select('h3 a.ui-link')
    for link in rcw_links:
        if 'RCW/default.aspx?cite=' in link.get('href', ''):
            rcw_number = link.text.strip()
            break
    
    if not rcw_number:
        # Alternative approach - look for the cite in the URL
        cite_match = re.search(r'cite=(\d+\.\d+\.\d+)', section_url, re.IGNORECASE)
        if cite_match:
            rcw_number = cite_match.group(1)
    
    result['section_id'] = rcw_number
    
    # Try to find the section title
    title_element = soup.select_one('div h3:not(:has(a))')
    if title_element:
        result['title'] = title_element.text.strip()
    else:
        result['title'] = "Unknown Title"
    
    # Find the content divs - focusing on the main text content
    content_divs = soup.select('div div[style*="text-indent"]')
    if content_divs:
        # Join all indented text sections
        content_text = ' '.join([div.get_text(strip=True) for div in content_divs])
        result['text'] = content_text
    else:
        # Fallback - try different content selectors
        content_div = soup.find(id="contentstart") or soup.select_one('div.RCWSection') or soup.select_one('div#contentWrapper')
        if content_div:
            # Clean up the content by removing citations, etc.
            for citation in content_div.select('div[style*="margin-top"]'):
                citation.decompose()
            
            # Remove PDF links and other irrelevant elements
            for pdf_link in content_div.select('a[href*="pdf=true"]'):
                if pdf_link.parent and pdf_link.parent.name == 'h3':
                    pdf_link.decompose()
            
            content_text = content_div.get_text(strip=True, separator=' ')
            
            # Try to clean up the text to match the desired format
            # Remove the RCW number if it appears at the beginning
            if rcw_number and content_text.startswith(f"RCW {rcw_number}"):
                content_text = content_text[len(f"RCW {rcw_number}"):].strip()
            
            # Remove the title if it appears at the beginning
            if result['title'] and content_text.startswith(result['title']):
                content_text = content_text[len(result['title']):].strip()
            
            result['text'] = content_text
        else:
            result['text'] = "No content found"
    
    # Format the result to match your desired output
    formatted_text = f"RCW **{result['section_id']}**\n{result['title']}\n{result['text']}"
    
    print("=---------------------------------------------------------")
    print(formatted_text)
    print("=---------------------------------------------------------")

    return {
        'text': formatted_text,
        'citation_links': []  # Skip citation links as they're not needed
    }

def scrape_laws():
    """Scrape Washington State Laws from Titles 1 to 3."""
    # Create database if it doesn't exist
    create_db()
    
    # Process each title directly using the correct URLs
    for title_num, title_url in TITLE_URLS.items():
        print(f"\n🔍 Processing Title {title_num} ({title_url})")
        
        # Get chapter links
        chapter_links = extract_chapter_links(title_url, title_num)
        if not chapter_links:
            print(f"⚠️ No chapters found in Title {title_num} at {title_url}")
            continue
            
        print(f"Found {len(chapter_links)} chapters in Title {title_num}")
        
        for chapter_name, chapter_url in chapter_links:
            print(f"\n📌 Processing {chapter_name} ({chapter_url})")
            time.sleep(1)  # Be nice to the server
            
            # Get section links
            section_links = extract_section_links(chapter_url)
            if not section_links:
                print(f"⚠️ No sections found in {chapter_name} at {chapter_url}")
                continue
                
            print(f"Found {len(section_links)} sections in {chapter_name}")
            
            for section_id, section_url in section_links:
                print(f"📝 Processing section {section_id} ({section_url})")
                time.sleep(1)  # Be nice to the server
                
                # Get section content
                content = extract_section_content(section_url)
                if not content:
                    continue
                    
                # Save the section to the database
                save_to_db(
                    f"Title {title_num}", 
                    chapter_name, 
                    section_id, 
                    content['text'], 
                    section_url
                )
                
                # Optionally save citation links too
                for cite_text, cite_url in content['citation_links']:
                    print(f"  🔗 Citation: {cite_text} -> {cite_url}")

if __name__ == "__main__":
    print("Starting Washington State Law Crawler...")
    scrape_laws()
    print("\nCrawling completed.")