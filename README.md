# Scalable_webscraping_pipeline
This repository provides tools to extract contact information from  a public directory(specifically designed for Europages) focusing on different industry sectors at the same time. 
It includes functionality for:

  - Scraping company profiles.

  - Extracting and validating contact details (emails, websites, etc.).

  - Cleaning and deduplicating company and email records.

# Designed Features
Sector-based scraping: Search by industry or niche keywords.

Contact validation: Ensure emails are in a valid format and likely business-related.

Data cleaning: Remove duplicate companies and repeated email addresses.

Flexible configuration: Easily define sector links, pagination, and scraping parameters.

# Repository Structure: 

      📂 project_root
      │── contact_details_validation.py   # Email & contact validation utilities
      │── core_datastructures.py          # Core data classes (CompanyInfo, DirectoryConfig, ScrapingStats)
      │── DataProcessor.py                # Functions to deduplicate companies & emails
      │── README.md                       # User guide (this file)

# How to Search for Sectors in Europages
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
                                                      | Start: Define Sector     |
                                                      | Keyword                  |
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
