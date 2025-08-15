# CSVExporter.py

# Importing created modules
from core_datastructures import CompanyInfo

# helping modules
import csv                          # For writing CSV files
import logging                      # For logging export status
import os                          # For path operations
from typing import List             # For type hints


class CSVExporter:
    """
    Exporter class to write company data to CSV files.

    Responsibilities:
        - Save company links (name, country, Europages URL, website URL) to a CSV
        - Save extracted emails (name, country, website URL, email) to a CSV
        - Handle full file paths for organized output
    """

    @staticmethod
    def export_links(companies: List[CompanyInfo], filepath: str):
        """
        Export company links to a CSV file.

        Args:
            companies (List[CompanyInfo]): List of company data to export
            filepath (str): Full path for output CSV file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Open file in write mode with UTF-8 encoding
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row
            writer.writerow(['Name', 'URL', 'Country'])
            
            # Write one row per company
            for company in companies:
                writer.writerow([company.name, company.url, company.country])
        
        # Log successful export with full path
        logging.info(f"Exported {len(companies)} company links to {os.path.abspath(filepath)}")

    @staticmethod
    def export_links_with_websites(companies: List[CompanyInfo], filepath: str):
        """
        Export company data including website URLs to a CSV file.
        This creates the links CSV with: Company names, Countries, Europages URLs, and Company website URLs.

        Args:
            companies (List[CompanyInfo]): List of company data to export
            filepath (str): Full path for output CSV file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        # Open file in write mode with UTF-8 encoding
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row with Country included
            writer.writerow(['Company Name', 'Country', 'Europages URL', 'Company Website URL'])
            
            # Write one row per company
            for company in companies:
                writer.writerow([
                    company.name, 
                    company.country or "",  # Country field
                    company.url,  # This is the Europages URL
                    company.website_url or ""  # Company website URL (empty if not found)
                ])
        
        # Log successful export with full path
        logging.info(f"Exported {len(companies)} companies with website URLs and countries to {os.path.abspath(filepath)}")

    @staticmethod
    def export_emails(companies: List[CompanyInfo], filepath: str):
        """
        Export email addresses to a CSV file.

        Args:
            companies (List[CompanyInfo]): List of companies with extracted emails
            filepath (str): Full path for output CSV file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        # Open file in write mode with UTF-8 encoding
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row
            writer.writerow(['Name', 'Country', 'Email'])
            
            email_count = 0  # Track total exported emails
            
            # Write one row per email address found
            for company in companies:
                for email in company.emails:
                    writer.writerow([company.name, company.country, email])
                    email_count += 1
        
        # Log successful export with full path
        logging.info(f"Exported {email_count} emails to {os.path.abspath(filepath)}")

    @staticmethod
    def export_emails_with_websites(companies: List[CompanyInfo], filepath: str):
        """
        Export email addresses with website URLs to a CSV file.
        This creates the emails CSV with: Company names, Countries, company website URLs, emails extracted.

        Args:
            companies (List[CompanyInfo]): List of companies with extracted emails
            filepath (str): Full path for output CSV file
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        # Open file in write mode with UTF-8 encoding
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header row with Country included
            writer.writerow(['Company Name', 'Country', 'Company Website URL', 'Email'])
            
            email_count = 0  # Track total exported emails
            
            # Write one row per email address found
            for company in companies:
                if company.emails:  # Only include companies that have emails
                    for email in company.emails:
                        writer.writerow([
                            company.name, 
                            company.country or "",  # Country field
                            company.website_url or "",  # Company website URL
                            email
                        ])
                        email_count += 1
        
        # Log successful export with full path
        logging.info(f"Exported {email_count} emails with website URLs and countries to {os.path.abspath(filepath)}")