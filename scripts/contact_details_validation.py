#contact_details_validation.py

# Helping modules
import re  # For using regular expressions
import logging  # For logging debug messages
from typing import List, Set, Optional # For type annotations


class ContactValidator:
    """
    Description: 
    Aggregates all contact validation tools (e.g., email, phone, etc.).
    Extendable to include phone, website, LinkedIn, etc.
    
    Parameters
    custom_business_domains(Set(str)): Can include domains of specific sector 
                                       Ex: winery_domains = {'winery', 'vineyard', 'vignoble', 'weingut', 'vino', 'wine'}
    """

    def __init__(self, custom_business_domains: Optional[Set[str]] = None):
        
        self.email = EmailValidator(custom_business_domains)


class EmailValidator:
    """
    Description: A utility class for validating and identifying business email addresses.
    """
    def __init__(self, custom_business_domains: Optional[Set[str]] = None):
        self.personal_domains = {
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',"email.com",
            'aol.com', 'icloud.com', 'mail.com', 'protonmail.com','domain.com',
            "mysite.com","business.com","usercentrics.com","snazzymaps.com"
        }
        self.custom_business_domains = custom_business_domains or set()

    
    @staticmethod
    def is_valid_email(email)->bool:
        """
        Function: Validate the format of an email address using a regular expression.

        Parmeters:
            email (str): The email address to validate.

        Returns:
            bool: True if the email matches a valid format, False otherwise.
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}$'
        
        return re.match(pattern, email) is not None
    
    
    def is_business_email(self, email:str)->bool:
        """
        Function: Check if the email belongs to a business domain by filtering out common personal email providers.

        Parameters:
            email (str): The email address to evaluate.

        Returns:
            bool: True if the email is likely business-related, False if it's from a personal domains that belongs to personal_domains 
                  that contains 'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com','aol.com', 'icloud.com', 'mail.com', 'protonmail.com'
        """
        if "@" not in email:
            return False
            
        domain = email.split("@")[1].lower()
        
        # First check against custom business domains
        if domain in self.custom_business_domains:
            return True
            
        # Then check against personal domains
        return domain not in self.personal_domains
