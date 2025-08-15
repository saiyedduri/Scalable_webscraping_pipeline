# directory_parser.py

# Importing created modules
from webscraping import WebScrapingEngine
from core_datastructures import CompanyInfo

# Helping modules
import logging                                       # For logging errors and information during scraping
from typing import List, Dict, Set, Optional, Tuple  # For type annotations
from bs4 import BeautifulSoup                        # For pasing HTML content
from urllib.parse import urljoin                     # For resolving relative URLs to absolute
import hashlib                                       # For generating fallback name using MD5 hash
import re
from threading import Lock                           # For thread safety

class DirectoryParser:
    """
    Description: A parser to extract company profile links from directory-style web pages.

    Parameters:
        scraping_engine (WebScrapingEngine): Web scraping engine used to fetch and parse pages.
        seen_urls (Set[str]): Set to track and avoid duplicate company URLs.
    """

    def __init__(self, scraping_engine: WebScrapingEngine):
        """
        Function: Initialize the DirectoryParser.

        Parameters:
            scraping_engine (WebScrapingEngine): Instance used to fetch web pages.
        """
        self.engine = scraping_engine
        self.seen_urls: Set[str] = set()
        self.seen_urls_lock = Lock()  # Thread safety

    def extract_company_links(self, directory_url: str, 
                              link_selector: str,
                              pagination_selector: str = None,
                              max_pages: int = 5) -> List[CompanyInfo]:
        """
        Function: Extract company profile links from a directory, supporting pagination.

        Parameters:
            directory_url (str): The starting URL of the directory page.
            link_selector (str): CSS selector used to find company profile links.
            pagination_selector (str, optional): CSS selector to find the next page link.
            max_pages (int): Maximum number of pages to crawl. Defaults to 5.

        Returns:
            List[CompanyInfo]: A list of extracted companies with names and URLs.
        """
            
        companies = []                    # Store collected companies
        current_page = 1                  # Start from the first page
        current_url = directory_url       # Initial page URL

        while current_page <= max_pages:
            logging.info(f"Processing page {current_page}: {current_url}")

            # Fetch and parse the current page
            soup = self.engine.get_page(
                    current_url,
                    wait_for_element=link_selector)
            if not soup:
                break  # Stop if page couldn't be fetched

            # Extract company links from the page
            page_companies = self._extract_links_from_page(soup, link_selector, current_url)
            companies.extend(page_companies)

            # If pagination is enabled and we haven't reached the max page limit
            if pagination_selector and current_page < max_pages:
                # Find the next page URL
                next_url = self._find_next_page(soup, pagination_selector, current_url)
                if next_url and next_url != current_url:
                    current_url = next_url
                    current_page += 1
                else:
                    break  # No next page or stuck in a loop
            else:
                break  # No pagination selector or reached max pages

        return companies

    def _extract_links_from_page(self, soup: BeautifulSoup, 
                                 link_selector: str, 
                                 base_url: str) -> List[CompanyInfo]:
        """
        Function: Extract company links from a single parsed directory page.

        Parameters:
            soup (BeautifulSoup): Parsed HTML of the page.
            link_selector (str): CSS selector for finding company links.
            base_url (str): Base URL for resolving relative hrefs.

        Returns:
            List[CompanyInfo]: List of extracted company links with names and full URLs.
        """
        companies = []
        company_links = soup.select(link_selector)  # Find all matching link elements

        logging.info(f"Found {len(company_links)} company links on page")
        
        for link in company_links:
            href = link.get('href')
            if not href:
                continue  # Skip if no href present

            full_url = urljoin(base_url, href)  # Convert relative URL to full URL

            # Thread-safe duplicate check
            with self.seen_urls_lock:
                # Skip duplicates
                if full_url in self.seen_urls:
                    continue
                self.seen_urls.add(full_url)
            
            # Extract company name - try multiple approaches
            name = self._extract_company_name(link)
            
            companies.append(CompanyInfo(name=name, url=full_url))
        
        return companies
    
    def _extract_company_name(self, link) -> str:
        """
        Extract company name from link element using various strategies
        """
        # Strategy 1: Text content of the link itself
        name = link.get_text(strip=True)
        if name and len(name) > 1:  # Make sure it's not just a single character
            return name
            
        # Strategy 2: Look for span inside the link (common in Europages)
        name_span = link.select_one('span')
        if name_span:
            name = name_span.get_text(strip=True)
            if name and len(name) > 1:
                return name
        
        # Strategy 3: Look for other nested elements with text
        nested_elements = link.select('*')
        for element in nested_elements:
            text = element.get_text(strip=True)
            if text and len(text) > 1:
                return text
        
        # Strategy 4: Check title attribute
        title = link.get('title', '').strip()
        if title and len(title) > 1:
            return title
        
        # Strategy 5: Check aria-label attribute
        aria_label = link.get('aria-label', '').strip()
        if aria_label and len(aria_label) > 1:
            return aria_label
            
        # Strategy 6: Extract from URL path
        href = link.get('href', '')
        if href:
            # Clean URL and extract company identifier
            # For Europages URLs like: /CANARY-ISLAND-WORLDWIDE-SL/00000005425544-763896001.html
            path_parts = href.strip('/').split('/')
            if path_parts and len(path_parts) > 0:
                company_part = path_parts[0]
                
                # Remove file extensions
                company_part = re.sub(r'\.\w+$', '', company_part)
                
                # Remove trailing numbers and hashes (like the ID part)
                company_part = re.sub(r'-\d+.*$', '', company_part)
                
                # Replace hyphens and underscores with spaces
                name = company_part.replace('-', ' ').replace('_', ' ')
                
                # Clean up extra spaces
                name = re.sub(r'\s+', ' ', name).strip()
                
                if name and len(name) > 1:
                    # Convert to title case for better readability
                    return name.title()

    def _find_next_page(self, soup: BeautifulSoup, 
                    pagination_selector: str, 
                    current_url: str) -> Optional[str]:
        """
        Function: Locate the next page URL from the current page using the pagination selector.

        Parameters:
            soup (BeautifulSoup): Parsed HTML content of the current directory page.
            pagination_selector (str): CSS selector to identify the "next" page link.
            current_url (str): The URL of the current page, used to resolve relative links.

        Returns:
            Optional[str]: Full URL of the next page, or None if not found.
        """
        # With the provided selector
        next_link = soup.select_one(pagination_selector)
        if next_link and next_link.get('href'):
            return urljoin(current_url, next_link['href'])
        
        # Fallback to common pagination patterns if provided selector fails
        fallback_selectors = [
            'a[aria-label="Next page"]',
            '.pagination a[rel="next"]',
            '.pagination .next',
            'a:contains("Next")',
            'a[href*="pg-"]'
        ]
        
        for selector in fallback_selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get('href'):
                return urljoin(current_url, next_link['href'])
        
        return None
