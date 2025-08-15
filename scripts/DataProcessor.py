# DataProcessor.py

# Importing created modules
from core_datastructures import CompanyInfo

# Helping modules
from typing import List, Dict, Set, Optional, Tuple  # For type annotations


class DataProcessor: 
    """Process and clean extracted data"""

    @staticmethod
    def deduplicate_companies(companies: List[CompanyInfo]) -> List[CompanyInfo]:
        """
        Remove duplicate companies based on URL.
        
        Parameters:
            companies (List[CompanyInfo]): List of extracted company data.

        Returns:
            List[CompanyInfo]: List with duplicate companies removed.
        """
        seen_urls = set()  # Track URLs we've already encountered
        unique_companies = []  # Store only unique company entries

        # Iterate through all companies
        for company in companies:
            # If the company's URL hasn't been seen, it's unique
            if company.url not in seen_urls:
                seen_urls.add(company.url)  # Mark URL as seen
                unique_companies.append(company)  # Add company to result list

        return unique_companies

    @staticmethod
    def deduplicate_emails(companies: List[CompanyInfo]) -> List[CompanyInfo]:
        """
        Remove duplicate email addresses across all companies.
        
        Parameters:
            companies (List[CompanyInfo]): List of companies with emails.

        Returns:
            List[CompanyInfo]: Companies with duplicate emails removed.
        """
        seen_emails = set()  # Track all emails seen so far

        # Iterate over each company
        for company in companies:
            unique_emails = []  # Store only unique emails for this company

            # Check each email in the company's list
            for email in company.emails:
                if email not in seen_emails:
                    seen_emails.add(email)  # Mark email as seen
                    unique_emails.append(email)  # Keep the email

            # Update company with de-duplicated emails
            company.emails = unique_emails

        return companies