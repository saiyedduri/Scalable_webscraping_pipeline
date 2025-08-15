# BusinessScrapingpipeline.py 

# Importing created modules
from contact_details_validation import ContactValidator
from core_datastructures import CompanyInfo
from webscraping import WebScrapingEngine
from directory_parser import DirectoryParser
from DataProcessor import DataProcessor
from contact_extraction import ContactExtractor  
from CSVExporter import CSVExporter

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


# Helping modules
from typing import List, Dict, Set, Optional, Tuple  # For type annotations
import logging                                       # For logging errors and information during scraping
import time                                          # For adding delays between requests
import os                                            # For creating directories
from pathlib import Path                            # For path operations
from datetime import datetime                       # For timestamping


class BusinessScrapingPipeline: 
    """
    Description: Main pipeline orchestrator for scraping business directories with enhanced multi-page contact extraction.

    Responsibilities:
        - Coordinate extraction of company links from directory pages
        - Remove duplicates and clean data
        - Extract contact emails from company pages (homepage + contact pages)
        - Export data to CSV files in results folder

    Parameters:
        use_selenium (bool): Whether to enable Selenium for dynamic page scraping
        custom_business_domains (Optional[Set[str]]): Custom set of business domain keywords for email validation.
        results_dir (str): Directory to save all output files.
    """
    
    def __init__(self, 
                 use_selenium: bool = False,
                 custom_business_domains: Optional[Set[str]] = None,
                 results_dir: str = "results"):
        
        # Initialize the web scraping engine with or without Selenium
        self.engine = WebScrapingEngine(use_selenium=use_selenium)
        self.custom_business_domains = custom_business_domains
        self.results_dir = results_dir

        # Create results directory if it doesn't exist
        self.setup_results_directory()

        # Instantiate helper components
        self.parser = DirectoryParser(self.engine)
        self.extractor = ContactExtractor(self.engine, self.custom_business_domains)  # Enhanced version
        self.processor = DataProcessor()
        self.exporter = CSVExporter()
    
    def setup_results_directory(self):
        """
        Function: Create results directory if it doesn't exist.
        """
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)
        logging.info(f"Results directory ready: {self.results_dir}")
    
    def get_results_path(self, filename: str) -> str:
        """
        Function: Get full path for file in results directory.

        Parameters:
            filename (str): Name of the file to create path for.

        Returns:
            str: Full path combining results directory and filename.
        """
        return os.path.join(self.results_dir, filename)
    
    def run_pipeline(self, sector: str, directory_config: Dict, limit_companies: Optional[int] = None):
        """
        Function: Run the complete scraping pipeline with enhanced multi-page contact extraction.

        Parameters:
            sector (str): The business category to scrape (e.g., 'cnc_machinery')
            directory_config (Dict): Configuration dictionary with keys:
                - 'url': Starting directory page URL
                - 'link_selector': CSS selector to extract company links
                - 'pagination_selector': CSS selector for pagination (optional)
                - 'max_pages': Max number of directory pages to scrape (optional)
                - 'business_domain_keywords': Set of domain keywords for email validation
            limit_companies (Optional[int]): Limit processing to first N companies (for testing)
        """
        logging.info(f"Starting enhanced pipeline for sector: {sector}")
        logging.info(f"Enhanced features: Multi-page contact extraction, contact page discovery")
        
        try:
            # Step 1: Extract company links from directory
            logging.info("Step 1: Extracting company links...")

            # Update extractor with sector-specific domains
            domain_keywords = directory_config.get('business_domain_keywords', set())
            self.extractor.validator.email.custom_business_domains = domain_keywords
            
            companies = self.parser.extract_company_links(
                directory_url=directory_config['url'],
                link_selector=directory_config['link_selector'],
                pagination_selector=directory_config.get('pagination_selector'),
                max_pages=directory_config.get('max_pages', 2))
            
            # Step 2: Remove duplicate company entries based on URL
            companies = self.processor.deduplicate_companies(companies)
            logging.info(f"Found {len(companies)} unique companies")
            
            # Apply limit if specified (for testing)
            if limit_companies:
                companies = companies[:limit_companies]
                logging.info(f"Limited to first {len(companies)} companies for testing")
            
            # Step 3: Extract website URLs and update company objects
            logging.info("Step 2: Extracting company website URLs...")

            companies_with_websites = self.extractor.extract_website_urls(companies)
            logging.info("Company website extraction completed")
            
            # Step 4: Export company data with website URLs to CSV in results folder
            links_filename = f"links_{sector}_found_{len(companies)}.csv"
            links_path = self.get_results_path(links_filename)
            self.exporter.export_links_with_websites(companies_with_websites, links_path)
            
            # Step 5: Enhanced email extraction with multi-page contact discovery
            logging.info("Step 3: Extracting contact information with enhanced multi-page search...")
            logging.info("Enhanced features active: Contact page discovery,improved email patterns")
            
            companies_with_contacts = []
            
            # Process companies one by one to avoid threading issues
            for i, company in enumerate(companies_with_websites, 1):
                logging.info(f"\nProcessing company {i}/{len(companies_with_websites)}: {company.name}")
                logging.info(f"Website URL: {company.website_url}")
                
                # Initialize emails as empty list to ensure clean state
                company.emails = []
                
                if company.website_url and company.website_url.strip():
                    try:
                        # Email extraction - automatically checks contact pages
                        logging.info(f"Starting enhanced email extraction for {company.name}...")
                        extracted_emails = self.extractor._extract_emails_from_website(company.website_url, company.name)
                        company.emails = extracted_emails
                        
                        if company.emails:
                            companies_with_contacts.append(company)
                            logging.info(f"SUCCESS: Found {len(extracted_emails)} emails for {company.name}")
                            logging.info(f"Emails discovered: {extracted_emails}")
                        else:
                            logging.info(f"No emails found for {company.name} after checking multiple pages")
                            
                    except Exception as e:
                        logging.error(f"ERROR extracting emails for {company.name}: {e}")
                        company.emails = []
                else:
                    logging.warning(f"No website URL for {company.name}")
                    company.emails = []
                
                # Increased delay between companies since we're checking more pages
                logging.info(f"Pausing 3 seconds before next company...")
                time.sleep(3)
            
            # Step 6: Remove duplicate emails across companies
            companies_with_contacts = self.processor.deduplicate_emails(companies_with_contacts)
            
            # Step 7: Export extracted email data to CSV in results folder
            emails_filename = f"emails_{sector}_found_{len(companies_with_contacts)}.csv"
            emails_path = self.get_results_path(emails_filename)
            self.exporter.export_emails_with_websites(companies_with_contacts, emails_path)
            
            # Final summary with enhanced extraction stats
            logging.info(f"\nENHANCED PIPELINE COMPLETED for {sector}")
            logging.info(f"Final results: {len(companies_with_contacts)} companies with contacts found")
            logging.info(f"All files saved to: {self.results_dir}")
            
            # Additional statistics
            total_emails_found = sum(len(company.emails) for company in companies_with_contacts)
            avg_emails_per_company = total_emails_found / max(len(companies_with_contacts), 1)
            success_rate = (len(companies_with_contacts) / max(len(companies_with_websites), 1)) * 100
            
            logging.info(f"Enhancement Statistics:")
            logging.info(f"   - Total emails extracted: {total_emails_found}")
            logging.info(f"   - Average emails per company: {avg_emails_per_company:.2f}")
            logging.info(f"   - Success rate: {success_rate:.1f}%")

        except Exception as e:
            logging.error(f"Pipeline failed for {sector}: {e}")
            raise

    def get_summary_report(self) -> str:
        """
        Function: Generate a summary of files in the results directory with enhanced extraction info.

        Returns:
            str: Formatted report of all files in results directory.
        """
        if not os.path.exists(self.results_dir):
            return f"Results directory '{self.results_dir}' not found."
        
        files = os.listdir(self.results_dir)
        if not files:
            return f"Results directory '{self.results_dir}' is empty."
        
        report = f"\n=== ENHANCED SCRAPING RESULTS SUMMARY ===\n"
        report += f"Results saved to: {os.path.abspath(self.results_dir)}\n"
        report += f"Enhanced features: Multi-page contact extraction, contact page discovery\n\n"
        
        csv_files = [f for f in files if f.endswith('.csv')]
        log_files = [f for f in files if f.endswith('.log')]
        other_files = [f for f in files if not f.endswith('.csv') and not f.endswith('.log')]
        
        if csv_files:
            report += f"CSV Files ({len(csv_files)}):\n"
            for csv_file in sorted(csv_files):
                full_path = os.path.join(self.results_dir, csv_file)
                size = os.path.getsize(full_path)
                
                # Enhanced info for email files
                if csv_file.startswith('emails_'):
                    report += f"  {csv_file} ({size:,} bytes) [Enhanced multi-page extraction]\n"
                elif csv_file.startswith('links_'):
                    report += f"  {csv_file} ({size:,} bytes) [Company links with websites]\n"
                else:
                    report += f"  {csv_file} ({size:,} bytes)\n"
        
        if log_files:
            report += f"\nLog Files ({len(log_files)}):\n"
            for log_file in sorted(log_files):
                full_path = os.path.join(self.results_dir, log_file)
                size = os.path.getsize(full_path)
                report += f"  {log_file} ({size:,} bytes)\n"
        
        if other_files:
            report += f"\nOther Files ({len(other_files)}):\n"
            for other_file in sorted(other_files):
                report += f"  {other_file}\n"
        
        report += f"\nTotal files: {len(files)}\n"
        report += f"Enhancement note: Email extraction now includes contact page discovery\n"
        return report


def setup_logging_in_results(results_dir: str = "results") -> None:
    """
    Function: Setup logging to save debug_scraping.log in the results directory with enhanced extraction info.
    
    Parameters:
        results_dir (str): Directory where log file should be saved
    """
    # Create results directory if it doesn't exist
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"debug_log_{timestamp}.log"
    log_path = os.path.join(results_dir, log_filename)
    
    # Configure detailed logging to save in results directory
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path),
            logging.StreamHandler() 
        ]
    )
    
    logging.info(f"Enhanced logging initialized. Log file: {log_path}")
    logging.info(f"Enhanced features: Multi-page contact extraction, contact page discovery")


def main():
    """
    Function: Entry point for executing the enhanced business scraping pipeline.
    Defines sector-specific configurations and runs the pipeline for each.
    """
    # Define results directory
    results_dir = "results"
    
    # Setup enhanced logging to save in results directory
    setup_logging_in_results(results_dir)
    
    logging.info("Starting Enhanced Business Scraping Pipeline")
    logging.info("New features: Multi-page contact extraction, contact page discovery")

    # Defining wine-specific sector email domains
    wine_domains = {
        'winery', 'vineyard', 'vignoble', 'weingut', 'vino', 'wine',
        'domaine', 'chateau', 'bodega', 'cantina', 'vinicola'
    }

    # Define CNC/machinery-specific domain keywords for email validation
    cnc_domains = {
        'cnc', 'machining', 'mechanical', 'precision', 'manufacturing', 
        'metal', 'turning', 'milling', 'industrial', 'engineering',
        'metalworking', 'fabrication', 'tooling', 'automation'
    }

    energy_storage_domains = {
    'energy', 'storage', 'battery', 'power', 'renewable', 'solar', 'wind',
    'grid', 'electrical', 'energytech', 'lithium', 'storagebattery', 'greenenergy',
    'cleanenergy', 'energytech', 'storagepower'}

    pharma_domains = {
    'pharma', 'pharmaceutical', 'biotech', 'biotech', 'health', 'healthcare', 
    'med', 'medicine', 'clinical', 'drug', 'therapeutics', 'life-sciences', 
    'lifescience', 'bioscience', 'medtech', 'biopharma'}

    textile_domains = {
    'textile', 'fabric', 'apparel', 'clothing', 'garment', 'fashion', 'weaving',
    'knitting', 'yarn', 'cotton', 'wool', 'synthetic', 'fiber', 'textiles', 
    'garments', 'cloth', 'tailoring'}



    # Directory configurations with correct domain keywords
    directories = {
        'dairy_products': {
        'url': 'https://www.europages.co.uk/companies/dairy%20products.html',
        'link_selector': 'a[data-test="company-name"]',
        'pagination_selector': 'a[aria-label="Next page"]',
        'max_pages': 2,
        'business_domain_keywords': []
        }
        }
    
    # Initialize the enhanced pipeline with Selenium support and results directory
    pipeline = BusinessScrapingPipeline(
        use_selenium=True,
        custom_business_domains=None,  # Use specific email domain keyword of the sector if required
        results_dir=results_dir)
    
    logging.info("pipeline initialized with multi-page contact extraction")
    
    # Execute the scraping pipeline for each configured sector
    for sector, config in directories.items():
        logging.info(f"\n{'='*60}")
        logging.info(f"STARTING  SECTOR: {sector.upper()}")
        logging.info(f"Features: Contact page discovery")
        logging.info(f"{'='*60}")
        
        try:
            # Run with your desired limit (e.g., 10 companies)
            pipeline.run_pipeline(sector, config, limit_companies=20)
            
            logging.info(f"COMPLETED ENHANCED SECTOR: {sector.upper()}")
            
        except Exception as e:
            logging.error(f"SECTOR FAILED: {sector.upper()} - {e}")
            
        # 10s gap between sectors (increased due to more intensive extraction)
        logging.info(f"Waiting 10 seconds before next sector...")
        time.sleep(10)
    
    # Print enhanced final summary
    logging.info(f"\nENHANCED PIPELINE COMPLETE!")
    print("\n" + "="*80)
    print("ENHANCED BUSINESS SCRAPING PIPELINE COMPLETED!")
    print("="*80)
    print(pipeline.get_summary_report())
    print("="*80)


# Execute the main function if this script is executed directly
if __name__ == "__main__":
    main()