#webscraping.py

# Helping modules
import requests                             # For sending HTTP requests to fetch web pages
import logging                              # For logging errors, warnings, and informational messages
import time                                 # For adding delays to simulate human browsing
import random                               # For generating random delay durations to avoid bot detection
from bs4 import BeautifulSoup               # For parsing and navigating HTML content
from threading import Lock                  # For ensuring thread-safe access to shared resources

from selenium import webdriver                          # To automate browser interactions using Selenium
from selenium.webdriver.common.by import By             # To locate HTML elements using selectors (e.g., CSS)
from selenium.webdriver.chrome.options import Options   # To configure Chrome WebDriver options (e.g., headless mode)
from selenium.webdriver.support.ui import WebDriverWait # To wait for elements to load on the page
from selenium.webdriver.support import expected_conditions as EC  # Predefined conditions to use with WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException  # Exceptions for handling loading and element errors


class WebScrapingEngine:
    """
    Description:
    Core web scraping utility that supports both static and dynamic content fetching.
    
    Uses 'requests and beautiful soup' for static pages and 'Selenium' for JavaScript-rendered content.
    
    Parameters:
        use_selenium (bool): Whether to use Selenium for page loading.
        session (requests.Session): Reusable session for HTTP requests.
        driver (webdriver.Chrome): Selenium WebDriver instance.
        lock (Lock): Thread-safe lock to control concurrent access.
    """
    
    def __init__(self, use_selenium: bool = False, headless: bool = True):
        self.use_selenium = use_selenium # Store whether to use Selenium for dynamic content scraping
        self.session = requests.Session() # Create a requests session for efficient HTTP requests
        self.driver = None # Initialize driver to None; will be set if Selenium is used
        self.lock = Lock()# Create a lock for thread-safe operations when scraping concurrently
        
        # Set a custom user-agent to mimic a real browser and avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        
        # If Selenium is enabled, set up the browser driver
        if use_selenium:
            self._setup_selenium(headless)
    
    def _setup_selenium(self, headless: bool):
        """
        Function: Set up Selenium Chrome WebDriver with specified options.

        Parameters:
            headless (bool): Run the browser in headless mode if True.
        """
        # Initialize browser options
        chrome_options = Options()

        # Run browser in headless mode
        if headless:
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--disable-gpu')
        
        # Recommended settings for running in restricted environments
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Anti-detection measures
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user-agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')
    
        try:
            # Attempt to start the Chrome WebDriver with options
            self.driver = webdriver.Chrome(options=chrome_options)
            # Set a timeout to prevent hanging on slow-loading pages
            self.driver.set_page_load_timeout(45)
        except Exception as e:
            # If setup fails, log the error and fall back to requests
            logging.warning(f"Selenium setup failed: {e}. Falling back to requests.")
            self.use_selenium = False
    
    def get_page(self, url: str, wait_for_element: str = None) -> BeautifulSoup:
        """
        Function: Fetch and parse a web page using requests or Selenium.

        Parameters:
            url (str): The URL of the web page to fetch.
            wait_for_element (str, optional): CSS selector to wait for (Selenium only).

        Returns:
            BeautifulSoup: Parsed HTML content of the page, or None on failure.
        """
        try:
            # Decide which method to use based on configuration
            if self.use_selenium and self.driver:
                return self._get_page_selenium(url, wait_for_element)
            else:
                return self._get_page_requests(url)
        except Exception as e:
            logging.error(f"Critical error fetching {url}: {e}")
            # Attempt fallback to requests
            try:
                logging.warning("Attempting requests fallback")
                return self._get_page_requests(url)
            except Exception as fallback_e:
                logging.error(f"Fallback also failed: {fallback_e}")
            return None
    
    def _get_page_requests(self, url: str) -> BeautifulSoup:
        """
        Function: Fetch and parse a static web page using the requests library.

        Parameters:
            url (str): The URL to retrieve.

        Returns:
            BeautifulSoup: Parsed HTML content.
        """
        with self.lock:
            # Introduce delay to avoid triggering rate-limiting or bot detection
            time.sleep(random.uniform(1, 3))  # Rate limiting
        
        # Perform HTTP GET request
        response = self.session.get(url, timeout=25)

        # Raise exception for HTTP errors 
        response.raise_for_status()

        # Parse HTML content using BeautifulSoup
        return BeautifulSoup(response.content, 'html.parser')

    
    def _get_page_selenium(self, url: str, wait_for_element: str = None) -> BeautifulSoup:
        """
        Function: Fetch and parse a dynamic web page using Selenium WebDriver.

        Parameters:
            url (str): The URL to retrieve.
            wait_for_element (str, optional): CSS selector to wait for before parsing.

        Returns:
            BeautifulSoup: Parsed HTML content after JavaScript rendering.
        """
        with self.lock:
            time.sleep(random.uniform(1, 3))
        
        self.driver.get(url)
        
        # Handle cookie consent
        try:
            consent_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button"))
            )
            consent_button.click()
            time.sleep(1)  # Allow page to settle
        except Exception as e:
            logging.debug(f"Cookie consent not found or not clickable: {e}")
        
        # Optionally wait for specific element
        if wait_for_element:
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            except TimeoutException:
                logging.warning(f"Timeout waiting for element {wait_for_element}")
        
        # Return the fully rendered page source
        return BeautifulSoup(self.driver.page_source, 'html.parser')


    def __del__(self):
        """
        Function: Clean up and close the Selenium WebDriver if it was initialized.
        """
        if self.driver:
            self.driver.quit()