# contact_extraction.py

# Importing created modules
from contact_details_validation import ContactValidator
from core_datastructures import CompanyInfo
from webscraping import WebScrapingEngine

# Helping modules
from typing import List, Dict, Set, Optional, Tuple
import re
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
import time

class ContactExtractor:
    """
    A class to extract contact information, such as email addresses and country, 
    from company web pages using a web scraping engine. Enhanced with multi-page 
    contact discovery including contact pages, about pages, and footer sections.

    Instances:
        engine (WebScrapingEngine): The web scraping engine used to fetch page content.
        validator (ContactValidator): Validator for processing and verifying contact details.
                                      custom_business_domains(Set(str)): Can include domains of specific sector 
                                         Ex: winery_domains = {'winery', 'vineyard', 'vignoble', 'weingut', 'vino', 'wine'}
    """
    def __init__(self, scraping_engine: WebScrapingEngine, custom_business_domains: Optional[Set[str]] = None):
        self.engine = scraping_engine
        self.validator = ContactValidator(custom_business_domains)
        
        # Common contact page URL patterns (in order of priority)
        self.contact_page_patterns = [
            '/contact', '/contact-us', '/contacts', '/contacto', '/contatti',
            '/about', '/about-us', '/about-company', '/chi-siamo', '/quienes-somos',
            '/info', '/information', '/company', '/empresa', '/societe',
            '/legal', '/mentions-legales', '/privacy', '/impressum',
            '/team', '/staff', '/equipe', '/equipo'
        ]
        
        # Contact page keywords for link text matching
        self.contact_keywords = {
            'english': ['contact', 'contact us', 'get in touch', 'reach us', 'about', 'about us', 'info'],
            'french': ['contact', 'contactez-nous', 'nous contacter', 'à propos', 'qui sommes-nous', 'info'],
            'spanish': ['contacto', 'contáctanos', 'acerca de', 'quiénes somos', 'sobre nosotros', 'info'],
            'italian': ['contatti', 'contattaci', 'chi siamo', 'informazioni', 'info'],
            'german': ['kontakt', 'über uns', 'impressum', 'info']
        }

    def extract_website_urls(self, companies: List[CompanyInfo]) -> List[CompanyInfo]:
        """
        Function: Extract website URLs from Europages profiles for all companies in the list.

        Parameters:
            companies (List[CompanyInfo]): List of companies with Europages URLs to process.

        Returns:
            List[CompanyInfo]: Companies with website_url and country fields populated.
        """
        updated_companies = []
        
        for company in companies:
            logging.info(f"Extracting website URL for: {company.name}")
            
            company.country = self._extract_country_from_profile(company.url)
            company.website_url = self._extract_website_from_profile(company.url)
            
            if not company.website_url:
                logging.warning(f"No website found for {company.name}")
                company.website_url = ""
            
            updated_companies.append(company)
        
        return updated_companies

    def _extract_emails_from_website(self, website_url: str, company_name: str = "") -> List[str]:
        """
        Function: Enhanced email extraction that checks multiple pages including contact pages for comprehensive email discovery.

        Parameters:
            website_url (str): The company website URL to scrape.
            company_name (str): Company name for logging purposes. Defaults to empty string.

        Returns:
            List[str]: List of valid business emails found across homepage and contact pages.
        """
        all_emails = set()
        pages_to_check = []
        
        try:
            logging.info(f"Starting enhanced email extraction for {company_name} at {website_url}")
            
            # Step 1: Always check the homepage first
            pages_to_check.append(('Homepage', website_url))
            
            # Step 2: Discover potential contact pages
            contact_pages = self._discover_contact_pages(website_url)
            pages_to_check.extend(contact_pages)
            
            # Step 3: Extract emails from each page
            for page_name, page_url in pages_to_check:
                try:
                    logging.info(f"Checking {page_name}: {page_url}")
                    page_emails = self._extract_emails_from_single_page(page_url, page_name)
                    
                    if page_emails:
                        all_emails.update(page_emails)
                        logging.info(f"Found {len(page_emails)} emails on {page_name}: {page_emails}")
                    
                    # Add delay between page requests
                    time.sleep(1.5)
                    
                    # Stop if we found enough emails to avoid over
                    if len(all_emails) >= 5:
                        logging.info(f"Found sufficient emails ({len(all_emails)}), stopping extraction")
                        break
                        
                except Exception as e:
                    logging.warning(f"Error extracting from {page_name} ({page_url}): {e}")
                    continue
            
            final_emails = sorted(list(all_emails))
            logging.info(f"Final email extraction result for {company_name}: {len(final_emails)} emails found")
            return final_emails
            
        except Exception as e:
            logging.error(f"Critical error in enhanced email extraction for {company_name}: {e}")
            return []

    def _discover_contact_pages(self, website_url: str) -> List[Tuple[str, str]]:
        """
        Function: Discover potential contact pages from the main website.

        Parameters:
            website_url (str): The main website URL to analyze for contact page links.

        Returns:
            List[Tuple[str, str]]: List of (page_name, page_url) tuples representing discovered contact pages.
        """
        contact_pages = []
        
        try:
            # Get the homepage to look for contact links
            soup = self.engine.get_page(website_url)
            if not soup:
                return self._generate_contact_urls_by_pattern(website_url)
            
            # Method 1: Look for contact links in navigation and footer
            contact_links = self._find_contact_links_in_page(soup, website_url)
            contact_pages.extend(contact_links)
            
            # Method 2: Generate common contact page URLs if no links found
            if len(contact_pages) < 3:
                pattern_urls = self._generate_contact_urls_by_pattern(website_url)
                contact_pages.extend(pattern_urls)
            
            # Remove duplicates while preserving order
            seen_urls = set()
            unique_pages = []
            for name, url in contact_pages:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_pages.append((name, url))
            
            # Limit to top 5 pages to avoid over-scraping
            return unique_pages[:5]
            
        except Exception as e:
            logging.warning(f"Error discovering contact pages for {website_url}: {e}")
            return self._generate_contact_urls_by_pattern(website_url)

    def _find_contact_links_in_page(self, soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
        """
        Function: Find contact-related links in the page navigation and content.

        Parameters:
            soup (BeautifulSoup): Parsed HTML content of the webpage.
            base_url (str): Base URL for resolving relative links to absolute URLs.

        Returns:
            List[Tuple[str, str]]: List of (page_name, page_url) tuples for discovered contact links.
        """
        contact_links = []
        
        # Areas to search for contact links (in order of priority)
        search_areas = [
            ('nav', soup.select('nav, .nav, .navigation, .navbar, .menu')),
            ('header', soup.select('header, .header')),
            ('footer', soup.select('footer, .footer')),
            ('main_menu', soup.select('.menu, .main-menu, #menu')),
            ('sidebar', soup.select('.sidebar, .side-nav')),
            ('content', [soup])  # Last resort: search entire page
        ]
        
        for area_name, elements in search_areas:
            for element in elements:
                links = element.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '').strip()
                    link_text = link.get_text().strip().lower()
                    
                    if not href or href.startswith('javascript:') or href.startswith('#'):
                        continue
                    
                    # Check if link text matches contact keywords
                    is_contact_link = False
                    for language, keywords in self.contact_keywords.items():
                        if any(keyword in link_text for keyword in keywords):
                            is_contact_link = True
                            break
                    
                    # Also check href for contact patterns
                    if not is_contact_link:
                        href_lower = href.lower()
                        if any(pattern in href_lower for pattern in self.contact_page_patterns):
                            is_contact_link = True
                    
                    if is_contact_link:
                        full_url = urljoin(base_url, href)
                        page_name = f"Contact ({link_text[:20]})" if link_text else "Contact Page"
                        contact_links.append((page_name, full_url))
        
        return contact_links

    def _generate_contact_urls_by_pattern(self, website_url: str) -> List[Tuple[str, str]]:
        """
        Function: Generate potential contact page URLs using common URL patterns.

        Parameters:
            website_url (str): Base website URL to append common contact page patterns to.

        Returns:
            List[Tuple[str, str]]: List of (page_name, page_url) tuples for generated contact page URLs.
        """
        contact_urls = []
        base_url = website_url.rstrip('/')
        
        for pattern in self.contact_page_patterns[:6]:  # Top 6 most common patterns
            contact_url = f"{base_url}{pattern}"
            page_name = f"Contact {pattern.replace('/', '').replace('-', ' ').title()}"
            contact_urls.append((page_name, contact_url))
        
        return contact_urls

    def _extract_emails_from_single_page(self, page_url: str, page_name: str) -> Set[str]:
        """
        Function: Extract email addresses from a single webpage using multiple detection methods.

        Parameters:
            page_url (str): The URL of the page to scrape for email addresses.
            page_name (str): Descriptive name of the page for logging purposes.

        Returns:
            Set[str]: Set of valid, cleaned email addresses found on the page.
        """
        found_emails = set()
        
        try:
            soup = self.engine.get_page(page_url)
            if not soup:
                return found_emails
            
            # Method 1: Extract from mailto links (most reliable)
            mailto_emails = self._extract_emails_from_mailto_links(soup)
            found_emails.update(mailto_emails)
            
            # Method 2: Extract from visible text (if no mailto found)
            if not found_emails:
                text_emails = self._extract_emails_from_text(soup.get_text())
                found_emails.update(text_emails)
            
            # Method 3: Look in specific contact areas
            contact_areas = soup.select(
                '.contact, .contact-info, .contacto, .contatti, '
                '.email, .mail, .footer, footer, '
                '[class*="contact"], [class*="email"], [class*="mail"]'
            )
            
            for area in contact_areas:
                area_emails = self._extract_emails_from_text(area.get_text())
                found_emails.update(area_emails)
                
                # Also check for mailto in this area
                area_mailto = self._extract_emails_from_mailto_links(area)
                found_emails.update(area_mailto)
            
            # Method 4: regex patterns for difficult cases
            page_html = str(soup)
            enhanced_emails = self._extract_emails_with_enhanced_patterns(page_html)
            found_emails.update(enhanced_emails)
            
            return found_emails
            
        except Exception as e:
            logging.warning(f"Error extracting emails from {page_name}: {e}")
            return found_emails

    def _extract_emails_with_enhanced_patterns(self, html_content: str) -> Set[str]:
        """
        Function: Extract emails using multiple enhanced regex patterns for difficult cases including encoded and obfuscated emails.

        Parameters:
            html_content (str): Raw HTML content of the webpage to search for email patterns.

        Returns:
            Set[str]: Set of valid, cleaned email addresses found using enhanced pattern matching.
        """
        found_emails = set()
        
        
        # Pattern 1: Emails with encoded characters (&#64; for @)
        pattern1 = r'\b[A-Za-z_-]+&#64;[A-Za-z-]+\.[A-Za-z]{2,6}\b'
        
        # Pattern 2: Emails split across HTML tags or with spaces
        pattern2 = r'\b[A-Za-z_-]+\s*@\s*[A-Za-z-]+\.[A-Za-z]{2,6}\b'
        
        # Pattern 3: JavaScript obfuscated emails
        pattern3 = r'["\']mailto:[^"\']*["\']'
        
        all_patterns = [pattern1, pattern2, pattern3]
        
        for pattern in all_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                # Clean up the match
                if 'mailto:' in match:
                    email = match.replace('mailto:', '').strip('\'"')
                elif '&#64;' in match:
                    email = match.replace('&#64;', '@')
                else:
                    email = re.sub(r'\s+', '', match)  # Remove spaces
                
                cleaned_email = self._clean_extracted_email(email)
                if cleaned_email:
                    found_emails.add(cleaned_email)
        
        return found_emails

    def _extract_emails_from_mailto_links(self, soup: BeautifulSoup) -> Set[str]:
        """
        Function: Extract and clean email addresses from all mailto: links on a page with enhanced cleaning.

        Parameters:
            soup (BeautifulSoup): Parsed HTML content of the page.

        Returns:
            Set[str]: Set of valid, cleaned email addresses from mailto links.
        """
        found_emails = set()
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href.startswith('mailto:'):
                # Handle complex mailto formats: mailto:email@domain.com?subject=...
                email_part = href.replace('mailto:', '').split('?')[0].split('&')[0]
                for email in email_part.split(','):
                    cleaned = self._clean_extracted_email(email)
                    if cleaned:
                        found_emails.add(cleaned)
                        logging.debug(f"Found mailto email: {cleaned}")
        
        return found_emails

    def _extract_emails_from_text(self, text: str) -> Set[str]:
        """
        Function: Extract and clean emails from a block of visible text using improved regex patterns.

        Parameters:
            text (str): Visible text content from a page or element.

        Returns:
            Set[str]: Set of valid, cleaned email addresses found in the text.
        """
        found_emails = set()
        if not text:
            return found_emails
        
        # More comprehensive regex pattern
        email_pattern = r'\b[A-Za-z](?:[A-Za-z0-9_-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9-_]*[A-Za-z])?\.[A-Za-z]{2,6}\b'
        
        matches = re.findall(email_pattern, text, re.IGNORECASE)
        for match in matches:
            cleaned = self._clean_extracted_email(match)
            if cleaned:
                found_emails.add(cleaned)
        
        return found_emails

    def _clean_extracted_email(self, email: str) -> Optional[str]:
        """
        Function: Clean and validate a single email address with improved parsing and spam filtering.

        Parameters:
            email (str): Raw email string that may contain extra text, HTML entities, or formatting.

        Returns:
            Optional[str]: Cleaned and validated email address, or None if invalid or spam.
        """
        if not email:
            return None
        
        # Remove common HTML entities and clean up
        email = email.replace('&#64;', '@').replace('&amp;', '&')
        email = email.strip('\n\r\t<>()[]{}",;:!?').lower()
        
        # Strict email validation regex
        email_match = re.match(r'^[a-z0-9]([a-z0-9._-]*[a-z0-9])?@[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,6}(\.[a-z]{2,3})?$', email)
        
        if not email_match:
            return None
        
        clean_email = email_match.group()
        
        # Validate using existing validator
        if not self.validator.email.is_valid_email(clean_email):
            return None
        
        if not self.validator.email.is_business_email(clean_email):
            logging.debug(f"Personal email filtered: {clean_email}")
            return None
        
        # Filter spam/placeholder emails
        spam_patterns = [
            'noreply', 'no-reply', 'donotreply', "example",'example.com', 'test@',"subscribe","unsubcribe","unsubscribe","cookiebot",
            'admin@localhost', 'info@example', 'contact@example', 'webmaster@',"commercial","privacy","email","domain","mail"
        ]
        
        if any(pattern in clean_email for pattern in spam_patterns):
            logging.debug(f"Spam email filtered: {clean_email}")
            return None
        
        return clean_email

    # Keep the existing methods from your original ContactExtractor
    def _is_valid_website_url(self, url: str) -> bool:
        """
        Function: Validate website URL format to ensure it starts with http:// or https:// and not a part of company official websites

        Parameters:
            url (str): URL string to validate.

        Returns:
            bool: True if URL has valid HTTP/HTTPS protocol, False otherwise.
        """
        if not url or not (url.startswith('http://') or url.startswith('https://')):
            return False

        # Domains we don't want to treat as company homepages
        unwanted_domains = [
            'hubspotusercontent', 'dropbox.com', 'drive.google.com',
            'onedrive.live.com', 'wetransfer.com', 'we.tl',
            's3.amazonaws.com', 'box.com', 'sharepoint.com',"adform"
        ]

        lowered_url = url.lower()
        if any(domain in lowered_url for domain in unwanted_domains):
            return False

        return True        
    
    def _extract_website_from_profile(self, profile_url: str) -> str:
        """
        Function: Extract company website URL from a Europages company profile page.

        Parameters:
            profile_url (str): The Europages company profile page URL.

        Returns:
            str: Company website URL if found, empty string otherwise.
        """
        try:
            soup = self.engine.get_page(profile_url, wait_for_element='.website-button')
            if not soup:
                return None
            
            # Look for website button
            website_button = soup.select_one('a.website-button, a[class*="website-button"]')
            
            if website_button and website_button.get('href'):
                website_url = website_button['href']
                if self._is_valid_website_url(website_url):
                    logging.info(f"Found website: {website_url}")
                    return website_url
            
            # Fallback methods (keep your existing fallback logic)
            external_links = soup.select('a[href^="http"]')
            for link in external_links:
                link_text = link.get_text().lower()
                if any(keyword in link_text for keyword in ['website', 'visit', 'site', 'homepage']):
                    href = link.get('href')
                    if href and self._is_valid_website_url(href):
                        return href
            return None
            
        except Exception as e:
            logging.error(f"Error extracting website from {profile_url}: {e}")
            return None
    
    def _extract_country_from_profile(self, profile_url: str) -> str:
        """
        Function: Extract country information from a Europages company profile page with enhanced and more accurate detection.

        Parameters:
            profile_url (str): The Europages company profile page URL.

        Returns:
            str: Country name if found, empty string otherwise.
        """
        try:
            soup = self.engine.get_page(profile_url)
            if not soup:
                return ""
            
            logging.info(f"Extracting country from profile: {profile_url}")
            
            # Initialize found_countries list at the beginning
            found_countries = []
            
            # Method 1: PRIORITY - Check for specific Europages country pattern
            europages_country = self._extract_europages_country_pattern(soup)
            if europages_country:
                found_countries.append((europages_country, 'Europages Pattern', 'span with data-v-fc5493f1'))
                logging.info(f"Found country via Europages pattern: {europages_country}")
            
            # Enhanced list of selectors to try (in order of priority)
            location_selectors = [
                # HIGHEST PRIORITY: Specific Europages country pattern
                'span[data-v-fc5493f1] + span[data-v-fc5493f1]',  # Country span after flag span
                'span.vis-flag + span',  # Country span after flag (vis-flag.de, etc.)
                'span[data-v-fc5493f1]:not([class*="flag"])',  # Any span with Vue data attribute that's not a flag
                '.vis-flag + span',  # Alternative flag + country pattern
                
                # HIGH PRIORITY: General country-specific patterns
                'span:contains("Germany")', 'span:contains("France")', 'span:contains("Italy")', 
                'span:contains("Spain")', 'span:contains("United Kingdom")', 'span:contains("Netherlands")',
                'span:contains("Belgium")', 'span:contains("Austria")', 'span:contains("Switzerland")',
                'span:contains("Poland")', 'span:contains("Czech Republic")', 'span:contains("Portugal")',
                
                # MEDIUM PRIORITY: Traditional selectors
                '[data-test="company-address"]',
                '[data-testid="company-address"]', 
                '.company-address',
                '.company-location',
                '.address-details',
                '.location-info',
                
                # Address containers
                '.address',
                '.location', 
                '.country',
                '.company-info .address',
                '.profile-address',
                '.contact-address',
                
                # Contact information areas
                '.contact-info',
                '.company-details',
                '.profile-info',
                '.company-profile',
                
                # Generic containers that might contain address
                '[class*="address"]', 
                '[class*="location"]',
                '[class*="country"]',
                '[class*="contact"]'
            ]
            
            # European countries list (comprehensive with variations)
            european_countries = {
                'france': 'France',
                'italy': 'Italy',
                'spain': 'Spain',
                'germany': 'Germany',
                'portugal': 'Portugal',
                'austria': 'Austria',
                'hungary': 'Hungary',
                'romania': 'Romania',
                'greece': 'Greece',
                'slovenia': 'Slovenia',
                'netherlands': 'Netherlands',
                'belgium': 'Belgium',
                'poland': 'Poland',
                'czech republic': 'Czech Republic',
                'slovakia': 'Slovakia',
                'croatia': 'Croatia',
                'bulgaria': 'Bulgaria',
                'estonia': 'Estonia',
                'latvia': 'Latvia',
                'lithuania': 'Lithuania',
                'malta': 'Malta',
                'cyprus': 'Cyprus',
                'luxembourg': 'Luxembourg',
                'ireland': 'Ireland',
                'denmark': 'Denmark',
                'sweden': 'Sweden',
                'finland': 'Finland',
                'united kingdom': 'United Kingdom',
                'uk': 'United Kingdom',
                'great britain': 'United Kingdom',
                'england': 'United Kingdom',
                'scotland': 'United Kingdom',
                'wales': 'United Kingdom',
                'northern ireland': 'United Kingdom',
                'switzerland': 'Switzerland',
                'norway': 'Norway',
                'iceland': 'Iceland',
                'turkey': 'Turkey',
                "US": 'United States',
                "USA": 'United States',
                "canaada": "Canada",
                
                # Additional variations and native names
                'deutschland': 'Germany',
                'espana': 'Spain',
                'españa': 'Spain',
                'italia': 'Italy',
                'nederland': 'Netherlands',
                'osterreich': 'Austria',
                'österreich': 'Austria',
                'ceska republika': 'Czech Republic',
                'česká republika': 'Czech Republic',
                'polska': 'Poland',
                'turkiye': 'Turkey',
                'türkiye': 'Turkey'
            }
            
            # Method 2: Try specific selectors with improved parsing (only if Europages pattern didn't work)
            if not found_countries:
                for selector in location_selectors:
                    try:
                        elements = soup.select(selector)
                        for element in elements:
                            text = element.get_text(strip=True).lower()
                            
                            # Skip if text is too long (likely not just an address)
                            if len(text) > 500:
                                continue
                                
                            logging.debug(f"Checking text from {selector}: {text[:100]}")
                            
                            # Look for country names in the text
                            for country_key, country_name in european_countries.items():
                                if country_key in text:
                                    # Additional validation: check if it's actually referring to the country
                                    if self._validate_country_context(text, country_key):
                                        found_countries.append((country_name, selector, text[:100]))
                                        logging.info(f"Found potential country via {selector}: {country_name}")
                                        break
                            
                            if found_countries:  # Break if we found something
                                break
                                            
                    except Exception as e:
                        logging.debug(f"Error with selector {selector}: {e}")
                        continue
                    
                    if found_countries:  # Break if we found something
                        break
            
            # Method 3: Enhanced URL-based detection (only if no other method worked)
            if not found_countries:
                url_country = self._extract_country_from_url(profile_url)
                if url_country:
                    found_countries.append((url_country, 'URL', profile_url))
                    logging.info(f"Found country from URL: {url_country}")
            
            # Method 4: Look for country in structured data (only if no other method worked)
            if not found_countries:
                structured_country = self._extract_country_from_structured_data(soup)
                if structured_country:
                    found_countries.append((structured_country, 'Structured Data', ''))
                    logging.info(f"Found country in structured data: {structured_country}")
            
            # Method 5: Meta tags and page metadata (only if no other method worked)
            if not found_countries:
                meta_country = self._extract_country_from_meta_tags(soup)
                if meta_country:
                    found_countries.append((meta_country, 'Meta Tags', ''))
                    logging.info(f"Found country in meta tags: {meta_country}")
            
            # Method 6: Search all text content as fallback (only if no other method worked)
            if not found_countries:
                all_text = soup.get_text().lower()
                for country_key, country_name in european_countries.items():
                    if country_key in all_text and self._validate_country_context(all_text, country_key):
                        found_countries.append((country_name, 'Full Text', ''))
                        logging.info(f"Found country in full text: {country_name}")
                        break
            
            # Determine the most reliable country from findings
            if found_countries:
                # Prioritize by method reliability (Europages pattern gets highest priority)
                method_priority = {
                    'Europages Pattern': 1,  # Highest priority for the specific pattern
                    'company-address': 2,
                    'address': 3,
                    'contact-info': 4,
                    'URL': 5,
                    'Structured Data': 6,
                    'Meta Tags': 7,
                    'Full Text': 8
                }
                
                # Sort by priority and return the most reliable result
                found_countries.sort(key=lambda x: method_priority.get(x[1], 99))
                best_country = found_countries[0][0]
                
                logging.info(f"Final country determination: {best_country} (from {found_countries[0][1]})")
                return best_country
            
            logging.warning(f"No country found for profile: {profile_url}")
            return ""
            
        except Exception as e:
            logging.error(f"Error extracting country from {profile_url}: {e}")
            return ""

    def _normalize_country_name(self, country_text: str) -> str:
        """
        Function: Normalize country name variations to standard names.
        
        Parameters:
            country_text (str): Raw country text to normalize
            
        Returns:
            str: Normalized country name or empty string if not recognized
        """
        if not country_text or len(country_text.strip()) == 0:
            return ""
        
        country_lower = country_text.strip().lower()
        
        # Country name mappings
        country_mappings = {
            'uk': 'United Kingdom',
            'great britain': 'United Kingdom',
            'england': 'United Kingdom',
            'scotland': 'United Kingdom',
            'wales': 'United Kingdom',
            'northern ireland': 'United Kingdom',
            'deutschland': 'Germany',
            'espana': 'Spain',
            'españa': 'Spain',
            'italia': 'Italy',
            'nederland': 'Netherlands',
            'osterreich': 'Austria',
            'österreich': 'Austria',
            'czech republic': 'Czech Republic',
            'ceska republika': 'Czech Republic',
            'česká republika': 'Czech Republic',
            'polska': 'Poland',
            'turkiye': 'Turkey',
            'türkiye': 'Turkey'
        }
        
        # Direct mapping
        if country_lower in country_mappings:
            return country_mappings[country_lower]
        
        # Check if it's already a proper country name
        proper_countries = [
            'France', 'Italy', 'Spain', 'Germany', 'Portugal', 'Austria',
            'Hungary', 'Romania', 'Greece', 'Slovenia', 'Netherlands',
            'Belgium', 'Poland', 'Czech Republic', 'Slovakia', 'Croatia',
            'Bulgaria', 'Estonia', 'Latvia', 'Lithuania', 'Malta',
            'Cyprus', 'Luxembourg', 'Ireland', 'Denmark', 'Sweden',
            'Finland', 'United Kingdom', 'Switzerland', 'Norway', 'Iceland'
        ]
        
        for country in proper_countries:
            if country.lower() == country_lower:
                return country
        
        return ""

    def _extract_europages_country_pattern(self, soup: BeautifulSoup) -> str:
        """
        Function: Extract country using Europages-specific HTML patterns.
        
        Parameters:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            str: Country name if found, empty string otherwise
        """
        try:
            # Look for flag + country pattern specifically used by Europages
            flag_elements = soup.select('span[data-v-fc5493f1]')
            
            for i, element in enumerate(flag_elements):
                # Check if this looks like a flag element (usually has a class with country code)
                element_class = element.get('class', [])
                element_class_str = ' '.join(element_class) if element_class else ''
                
                # Look for country code patterns in class names
                if any(code in element_class_str.lower() for code in ['flag', 'vis-']):
                    # The next span element often contains the country name
                    if i + 1 < len(flag_elements):
                        next_element = flag_elements[i + 1]
                        country_text = next_element.get_text(strip=True)
                        
                        if country_text and len(country_text) > 2:
                            normalized = self._normalize_country_name(country_text)
                            if normalized:
                                logging.info(f"Found country via Europages pattern: {normalized}")
                                return normalized
            
            # Alternative: look for spans immediately following flag-related elements
            flag_selectors = ['.vis-flag', '[class*="flag"]', '[class*="country"]']
            
            for selector in flag_selectors:
                flag_elements = soup.select(selector)
                for flag_element in flag_elements:
                    # Look for next sibling span
                    next_sibling = flag_element.find_next_sibling('span')
                    if next_sibling:
                        country_text = next_sibling.get_text(strip=True)
                        if country_text and len(country_text) > 2:
                            normalized = self._normalize_country_name(country_text)
                            if normalized:
                                return normalized
            
            return ""
            
        except Exception as e:
            logging.debug(f"Error in Europages country pattern extraction: {e}")
            return ""

    def _validate_country_context(self, text: str, country_key: str) -> bool:
        """
        Function: Validate that a country mention is in the right context.
        
        Parameters:
            text (str): Text containing the country name
            country_key (str): Country key to validate
            
        Returns:
            bool: True if the country mention seems legitimate
        """
        # Convert to lowercase for comparison
        text_lower = text.lower()
        
        # Positive indicators (address/location context)
        positive_indicators = [
            'address', 'location', 'based in', 'located in', 'from',
            'adresse', 'lieu', 'situé', 'dirección', 'ubicado'
        ]
        
        # Negative indicators (probably not an address)
        negative_indicators = [
            'ship to', 'delivery to', 'available in', 'markets in',
            'operates in', 'sells to', 'exports to'
        ]
        
        # Check for positive context
        has_positive_context = any(indicator in text_lower for indicator in positive_indicators)
        
        # Check for negative context
        has_negative_context = any(indicator in text_lower for indicator in negative_indicators)
        
        # If we have negative context, reject
        if has_negative_context:
            return False
        
        # If we have positive context or the text is short (likely just an address), accept
        if has_positive_context or len(text) < 200:
            return True
        
        # Default to accept if unsure
        return True

    def _extract_country_from_url(self, profile_url: str) -> str:
        """
        Function: Extract country information from URL patterns.
        
        Parameters:
            profile_url (str): URL to analyze
            
        Returns:
            str: Country name if detected from URL
        """
        try:
            url_lower = profile_url.lower()
            
            # URL-based country detection patterns
            url_country_patterns = {
                '/fr/': 'France',
                '/de/': 'Germany', 
                '/it/': 'Italy',
                '/es/': 'Spain',
                '/pt/': 'Portugal',
                '/nl/': 'Netherlands',
                '/be/': 'Belgium',
                '/at/': 'Austria',
                '/pl/': 'Poland',
                '/cz/': 'Czech Republic',
                '/uk/': 'United Kingdom',
                '/gb/': 'United Kingdom'
            }
            
            for pattern, country in url_country_patterns.items():
                if pattern in url_lower:
                    return country
            
            return ""
            
        except Exception as e:
            logging.debug(f"Error extracting country from URL: {e}")
            return ""

    def _extract_country_from_structured_data(self, soup: BeautifulSoup) -> str:
        """
        Function: Extract country from structured data (JSON-LD, microdata).
        
        Parameters:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            str: Country name from structured data
        """
        try:
            import json
            
            # Look for JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    
                    # Handle both single objects and arrays
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    
                    # Look for address information
                    address = data.get('address', {})
                    if isinstance(address, dict):
                        country = address.get('addressCountry', '')
                        if country:
                            normalized = self._normalize_country_name(country)
                            if normalized:
                                return normalized
                    
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
            
            return ""
            
        except Exception as e:
            logging.debug(f"Error extracting country from structured data: {e}")
            return ""

    def _extract_country_from_meta_tags(self, soup: BeautifulSoup) -> str:
        """
        Function: Extract country from meta tags.
        
        Parameters:
            soup (BeautifulSoup): Parsed HTML content
            
        Returns:
            str: Country name from meta tags
        """
        try:
            # Look for geo-related meta tags
            geo_tags = [
                'geo.country',
                'geo.region',
                'ICBM',
                'DC.coverage.spatial',
                'location'
            ]
            
            for tag_name in geo_tags:
                meta_tag = soup.find('meta', attrs={'name': tag_name})
                if meta_tag:
                    content = meta_tag.get('content', '')
                    if content:
                        normalized = self._normalize_country_name(content)
                        if normalized:
                            return normalized
            
            return ""
            
        except Exception as e:
            logging.debug(f"Error extracting country from meta tags: {e}")
            return ""