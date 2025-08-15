# Business Directory Scraping Pipeline

A comprehensive web scraping solution designed to extract business contact information from Europages directory with enhanced multi-page contact discovery and intelligent data validation.
## Overview

This pipeline orchestrates the extraction of company information from business directories, focusing on email discovery through enhanced multi-page analysis including contact pages, about pages, and footer sections.

![Alt text](my_image.png)


## Implemented Features

- Multi-page contact extraction with contact page discovery
- Industry-specific email validation
- Geographic data extraction with multilingual support
- Intelligent deduplication across companies
- Both Selenium and requests-based scraping
- Comprehensive data validation and cleaning
- Structured CSV export with detailed reporting

## Architecture Overview

### 1. Sector Selection

**Purpose:** Target specific industries for focused lead generation and improve email validation accuracy

- **Industry-Specific Targeting**: Defined sector-specific domain keywords (e.g., `wine_domains`, `cnc_domains`, `energy_storage_domains`) for enhanced email validation accuracy
  - *Purpose*: Filter out irrelevant emails and improve business email detection rates by recognizing industry-specific domains
- **Europages URL Mapping**: Created structured directory configurations mapping each sector to specific Europages category URLs (e.g., `/companies/wines.html`, `/companies/CNC.html`)
  - *Purpose*: Ensure targeted scraping of relevant businesses within specific industry verticals
- **Scalable Configuration**: Implemented dictionary-based sector definitions allowing easy addition of new industries
  - *Purpose*: Enable rapid expansion to new market segments without code modifications

### 2. Configuration

**Purpose:** Establish reliable, maintainable scraping parameters and handle dynamic content

- **CSS Selector Strategy**: Utilized Europages-specific selectors (`a[data-test="company-name"]`) for reliable profile link extraction and ensure consistent data extraction across Europages' standardized HTML structure
- **Pagination Handling**: Configured `aria-label="Next page"` selectors with `max_pages` limits  crawling scope and systematically traverse multiple directory pages while preventing infinite loops and server overload
- **Multi-Engine Support**: Implemented both Selenium and requests-based scraping with fallback mechanisms. It handles both static and JavaScript-rendered content while maintaining performance and reliability
- **Rate Limiting**: Built-in delays (1-3 seconds) and request throttling to avoid server overload It maintain ethical scraping practices and prevent IP blocking or server strain

### 3. Scraping

**Purpose:** Extract comprehensive business data including contact discovery across multiple pages

- **Multi-Page Architecture**:  Maximize data collection by accessing complete directory listings beyond first page. Sequential processing through directory pages using pagination selectors
- **Enhanced Data Extraction**: Ensure no company data is lost due to varying HTML structures.
  - Company names via multiple fallback strategies (link text, spans, URL parsing).
  - Country extraction using Europages-specific patterns and geographical context validation using geographic segmentation for targeted marketing campaigns
  - Website URL extraction from profile pages with anti-spam filtering to btain direct company websites for comprehensive contact discovery.
  - 
- **Contact Page Discovery**: Implemented intelligent contact page detection using URL patterns (`/contact`, `/about`) and multilingual keyword matching
  - *Purpose*: Significantly increase email discovery rates by checking dedicated contact pages beyond homepages

### 4. Validation

**Purpose:** Ensure data quality, filter spam, and maintain business-focused contact lists

#### Email Regex Patterns used:

```python
# Primary Pattern - Strict validation
r'^[a-z0-9]([a-z0-9._-]*[a-z0-9])?@[a-z0-9]([a-z0-9.-]*[a-z0-9])?\.[a-z]{2,6}(\.[a-z]{2,3})?$'
# Purpose: Strict validation ensuring only properly formatted email addresses are accepted

# Flexible Pattern - Context-aware extraction
r'\b[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,6}(?:\.[A-Za-z]{2,3})?\b'
# Purpose: Capture emails in varied text contexts with word boundaries

# Encoded Email Pattern - HTML entity handling
r'\b[A-Za-z_-]+&#64;[A-Za-z-]+\.[A-Za-z]{2,6}\b'
# Purpose: Extract emails obfuscated with HTML entities to bypass basic spam protection

# Spaced Email Pattern - Anti-scraping measures
r'\b[A-Za-z_-]+\s*@\s*[A-Za-z-]+\.[A-Za-z]{2,6}\b'
# Purpose: Capture emails with spacing used as anti-scraping measure

# JavaScript Obfuscated - Mailto links
r'["\']mailto:[^"\']*["\']'
# Purpose: Extract emails from JavaScript-protected mailto links
```

#### Email Validation Methods:

- **Business Email Filtering**: Excluded personal providers (`gmail.com`, `yahoo.com`, `hotmail.com`, `outlook.com`, `aol.com`, `icloud.com`, `mail.com`, `protonmail.com`)
  - *Purpose*: Focus on business contacts and eliminate personal email addresses for B2B targeting
- **Spam Pattern Detection**: Filtered emails containing `noreply`, `no-reply`, `donotreply`, `example`, `test@`, `admin@localhost`, `webmaster@`
  - *Purpose*: Remove non-actionable and placeholder emails to improve contact list quality
- **HTML Entity Decoding**: Converted `&#64;` to `@` and `&amp;` to `&`
  - *Purpose*: Normalize encoded characters for proper email format validation

### 5. Country Name Extraction Methods

**Purpose:** Enable geographic segmentation, market analysis, and region-specific targeting

#### Hierarchical Extraction Approach:

1. **Europages-Specific Pattern** (Highest Priority):
   ```python
   # Target selectors
   'span[data-v-fc5493f1] + span[data-v-fc5493f1]'  # Country span after flag span
   'span.vis-flag + span'  # Alternative flag + country pattern
   '.vis-flag + span'      # Additional flag pattern
   ```
   - *Purpose*: Leverage Europages' consistent flag+country display pattern for highest accuracy

2. **CSS Selector Hierarchy**:
   ```python
   selectors = [
       '[data-test="company-address"]',
       '.company-address', '.company-location', '.address-details',
       '.contact-info', '.company-details', '.profile-info',
       '[class*="address"]', '[class*="location"]', '[class*="country"]'
   ]
   ```
   - *Purpose*: Systematically check address-related elements in order of reliability

3. **Country Name Dictionary** (Multi-language Support):
   ```python
   european_countries = {
       'france': 'France', 'deutschland': 'Germany', 'espana': 'Spain',
       'italia': 'Italy', 'nederland': 'Netherlands', 'uk': 'United Kingdom',
       'österreich': 'Austria', 'ceska republika': 'Czech Republic'
       # ... more mappings
   }
   ```
   - *Purpose*: Handle multilingual country names and normalize to standard English format

4. **URL-Based Detection Patterns**:
   ```python
   url_country_patterns = {
       '/fr/': 'France', '/de/': 'Germany', '/it/': 'Italy',
       '/es/': 'Spain', '/uk/': 'United Kingdom'
   }
   ```
   - *Purpose*: Extract country information from URL structure as fallback method

5. **Context Validation**:
   ```python
   # Positive Indicators
   positive_indicators = [
       'address', 'location', 'based in', 'located in', 'adresse', 'lieu'
   ]
   
   # Negative Indicators  
   negative_indicators = [
       'ship to', 'delivery to', 'available in', 'exports to'
   ]
   ```
   - *Purpose*: Distinguish between company location and service areas to avoid misclassification

6. **Structured Data Extraction**: JSON-LD microdata parsing for `addressCountry` fields
   - *Purpose*: Leverage structured data markup for reliable country identification

7. **Meta Tag Analysis**: Geo-related tags (`geo.country`, `geo.region`, `DC.coverage.spatial`)
   - *Purpose*: Extract geographic metadata embedded by website developers

### 6. Cleaning

**Purpose:** Eliminate duplicates, standardize data format, and ensure dataset integrity

- **URL-Based Deduplication**: Removed duplicate companies using unique Europages URLs as primary keys
  - *Purpose*: Prevent duplicate companies in dataset and avoid redundant processing
- **Cross-Company Email Deduplication**: Eliminated duplicate emails across entire dataset to prevent contact overlap
  - *Purpose*: Ensure each business contact appears only once for clean marketing campaigns
- **Country Name Normalization**: Standardized variations (e.g., `UK` → `United Kingdom`, `Deutschland` → `Germany`)
  - *Purpose*: Enable consistent geographic analysis and filtering
- **Text Sanitization**: Applied `strip()`, lowercase conversion, and HTML entity cleanup
  - *Purpose*: Remove formatting artifacts and ensure clean, consistent text data

### 7. Export and Storage

**Purpose:** Provide organized, actionable datasets for business development and marketing activities

- **Structured CSV Output**: Generated two-tier export system:
  - **Links CSV**: Provide company discovery dataset for initial prospecting and research.
  - **Emails CSV**: Deliver actionable contact list ready for outreach campaigns
- **Results Directory Management**: Maintain organized data archives and enable process auditing
- **Comprehensive Reporting**: Enable performance monitoring, optimization decisions, and ROI assessment

## File Structure

```
📂
└── results/
└── scripts/
  ├── BussinessScrapingpipeline.py    # Main pipeline orchestrator
  ├── contact_details_validation.py   # Email validation and business filtering
  ├── contact_extraction.py          # Enhanced multi-page contact extraction
  ├── core_datastructures.py         # Data models and configuration classes
  ├── CSVExporter.py                 # CSV export functionality
  ├── DataProcessor.py               # Data cleaning and deduplication
  ├── directory_parser.py            # Directory page parsing and pagination
  ├── webscraping.py                 # Core scraping engine (Selenium + requests)
```

## Key Components

### WebScrapingEngine
- Dual-mode scraping (Selenium + requests)
- Anti-bot detection measures
- Automatic fallback mechanisms
- Rate limiting and ethical scraping practices

### ContactExtractor (Enhanced)
- Multi-page email discovery
- Contact page detection using URL patterns and keywords
- Advanced regex patterns for obfuscated emails
- Multilingual support for contact page discovery

### ContactValidator
- Industry-specific domain filtering
- Comprehensive spam detection
- Business vs. personal email classification

## Usage Example

```python
from BusinessScrapingPipeline import BusinessScrapingPipeline

# Define sector-specific domains
wine_domains = {
    'winery', 'vineyard', 'vignoble', 'weingut', 'vino', 'wine'
}

# Configure directory
directory_config = {
    'url': 'https://www.europages.co.uk/companies/wines.html',
    'link_selector': 'a[data-test="company-name"]',
    'pagination_selector': 'a[aria-label="Next page"]',
    'max_pages': 2,
    'business_domain_keywords': wine_domains
}

# Initialize pipeline
pipeline = BusinessScrapingPipeline(
    use_selenium=True,
    results_dir="results"
)

# Run scraping
pipeline.run_pipeline('wines', directory_config, limit_companies=20)
```

## Output Files

### Links CSV Format
```csv
Company Name,Country,Europages URL,Company Website URL
LA COMPAGNIE DE BURGONDIE,France,https://www.europages.co.uk/LA-COMPAGNIE-DE-BURGONDIE/00000005473718-001.html,https://www.burgondie.info/
CANARY ISLAND WORLDWIDE S.L.,Spain,https://www.europages.co.uk/CANARY-ISLAND-WORLDWIDE-SL/00000005425544-763896001.html,https://www.canaryislandworldwide.es
```

### Emails CSV Format
```csv
Company Name,Country,Company Website URL,Email
CANARY ISLAND WORLDWIDE S.L.,Spain,https://www.canaryislandworldwide.es,direccion@canaryislandworldwide.com
CANARY ISLAND WORLDWIDE S.L.,Spain,https://www.canaryislandworldwide.es,info@canaryislandworldwide.com
BODEGAS BOCOPA,Spain,https://www.bocopa.com/,enoteca@bocopa.com
```

## Performance Statistics

The pipeline provides comprehensive metrics:
- Total emails extracted
- Average emails per company  
- Success rate percentage
- Processing time and error counts
- Geographic distribution analysis

This architecture ensures robust, scalable, and maintainable business directory scraping with enterprise-grade data quality controls, multilingual support, and clear business value delivery at each stage.
