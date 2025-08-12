# Scalable_webscraping_pipeline
This repository aims tools to collect contact information of suppliers in various sectors from public contact directory (designed specifically for Europages) focusing on different industry sectors at the same time. 

The repository currently creates a database for  Bussiness email addresses, Company home pages. The pipeline can be easily extensible to collecting company contact numbers, and other details through adding further datastructures with Object oriented programming.

# Designed Features
  - Sector-based scraping: Search by industry or niche keywords.

  - Contact validation: Ensure emails are in a valid format and likely business-related.

  - Data cleaning: Remove duplicate companies and repeated email addresses.

  - Flexible configuration: Easily define sector links, pagination, and scraping parameters.

# Repository Structure: 

      📂 project_root
      project_root/
      │
      ├── /results
          
      
      │── scripts ── __pycache__/                # Compiled Python bytecode
                  │
                  ├── BussinessScrapingpipeline.py  # Main pipeline for business scraping
                  ├── contact_details_validation.py # Validation utilities for contact information
                  ├── contact_extraction.py         # Logic for extracting contact details from scraped data
                  ├── core_datastructures.py        # Core classes and data structures used across the project
                  ├── CSVExporter.py                # Module for exporting processed data to CSV files
                  ├── DataProcessor.py              # Data cleaning and transformation routines
                  ├── directory_parser.py           # Parses directory listings for data sources
                  ├── find_selectors.py             # Identifies CSS/HTML selectors for scraping
                  └── webscraping.py                 # Core web scraping logic
                  

# Parameters for setup of data collection pipeline: 
1. **Identify the sector keyword**
Examples: "winery", "machinery", "organic food", "IT services".
2. **Find the base URL on Europages**
3. **Configure DirectoryConfig** (in core_datastructures.py)
   Example:
   from core_datastructures import DirectoryConfig
      
         config = DirectoryConfig(
             name="Winery Sector",
             base_url="https://www.europages.com/companies/winery.html",
             sector_link=".company-name a",  # CSS selector for profile links
             paginatation_selector=".pagination a",
             max_pages=5,
             rate_limit_seconds=2.0)
   
  5. **Scrape company profiles**
        - Loop through sector pages.
        - Extract CompanyInfo objects.
  6. Validate & filter contact details
     Example: 
         from contact_details_validation import ContactValidator
         
         validator = ContactValidator(custom_business_domains={"winery", "vineyard"})
         is_valid = validator.email.is_valid_email("info@winery-example.com")
         is_business = validator.email.is_business_email("info@winery-example.com")

  7. Clean data
     from DataProcessor import DataProcessor

    companies = DataProcessor.deduplicate_companies(companies)
    companies = DataProcessor.deduplicate_emails(companies)

# Main Steps – Process Flow: A high-level process diagram for sector searching and data processing. 
                                                      +--------------------------+
                                                      | Start: Define multiple 
                                                        Sector                   |
                                                      | spefcific webpage
                                                        from directory           |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Set DirectoryConfig       |
                                                      | Parameters                |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Scrape Europages Sector  |
                                                      | Pages                    |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Extract CompanyInfo      |
                                                      | Objects                  |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Validate Email Formats   |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Check Business vs        |
                                                      | Personal Domains         |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Remove Duplicate         |
                                                      | Companies                |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Remove Duplicate Emails  |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      | Save & Export Clean Data |
                                                      +-----------+--------------+
                                                                  |
                                                                  v
                                                      +-----------+--------------+
                                                      |           End            |
                                                      +--------------------------+
                                                      
# Approach Summary
1.Sector Selection
  - Identify the industry keyword and relevant Europages URL.

2. Configuration
   - Set CSS selectors for profile links & pagination.

3. Scraping
   - Loop through pages, extract profile URLs, company names, countries, and contact details.

4. Validation
    - Use regex-based email format checks.
  
    - Filter out personal email providers.
  
    - Cleaning
  
    - Deduplicate by company URL.
  
    - Deduplicate emails across companies.
  
    - Export and Store results as CSV
