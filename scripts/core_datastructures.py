# core_datastructures.py

# Importing created modules
from dataclasses import dataclass # For creating simple data classes to store structured data

# Helping modules
from typing import List, Dict, Set, Optional, Tuple  # For type annotations

@dataclass
class CompanyInfo:
    """
    Description: class for storing company-related information scraped from directories.

    Parameters:
        name (str): The name of the company.
        url (str): The URL of the company's profile or official site (Europages URL).
        website_url (str): The actual company website URL extracted from profile.
        country (str): Optional country of the company. Defaults to empty string.
        emails (List[str]): A list of extracted email addresses. Initialized as an empty list if not provided.
    """
    name: str
    url: str  # This will be the Europages URL
    website_url: str = ""  # This will be the actual company website
    country: str = ""
    emails: List[str] = None

    def __post_init__(self):
        if self.emails is None:
            self.emails = []

@dataclass
class DirectoryConfig:
    """
    Function: Configuration for scraping a specific online directory.

    Parameters:
        name (str): Name or identifier of the directory or sector.
        base_url (str): The main URL from which scraping begins.
        sector_link (str): CSS selector used to find company profile links on the page.
        paginatation_selector (Optional[str]): CSS selector to locate the pagination link/button. Optional.
        max_pages (int): Maximum number of pages to scrape. Prevents infinite crawling. Default is 5.
        use_selenium (bool): Indicates whether Selenium should be used (for dynamic content). Default is False.
        wait_element (Optional[str]): CSS selector to wait for before scraping, if using Selenium. Optional.
        rate_limit_seconds (float): Time to wait (in seconds) between requests to avoid server overload. Default is 2.0.
    """
    name:str 
    base_url:str 
    sector_link:str
    paginatation_selector:Optional[str] = None 
    max_pages:int=5
    use_selenium:bool=False 
    wait_element: Optional[str]= None 
    rate_limit_seconds: float = 2.0

    def __post_init__(self):
        """Function: Validates the configuration for error handling."""
        if not self.name or not self.base_url or not self.sector_link:
            raise ValueError("name, base_url, and link_selector are required")

@dataclass
class ScrapingStats:
    """
    Function: Tracks statistics about a scraping run.

    Parameters:
        companies_found (int): Number of companies found (profile links extracted).
        companies_processed (int): Number of companies fully scraped and processed.
        emails_extracted (int): Total number of emails extracted.
        errors_encountered (int): Number of scraping errors encountered.
        processing_time_seconds (float): Total time taken for scraping (in seconds).
    """
    companies_found:int=0
    companies_processed:int=0
    emails_extracted:int=0
    errors_encountered:int=0
    processing_time_seconds:float=0.0

    def to_dict(self)-> Dict:
        return {
            "companies_found": self.companies_found,
            "companies_processed": self.companies_processed,
            "emails_extracted":self.emails_extracted,
            "errors_encountered":self.errors_encountered,
            "processing_time_seconnds": self.processing_time_seconds,
            "success_rate": self.companies_processed / max(self.companies_found, 1) * 100 }