#!/usr/bin/env python3
"""
Europages Selector Testing Tool
Use this to find the correct CSS selectors before running the main pipeline
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from webscraping import WebScrapingEngine
import logging
import json
from typing import Dict, List
import re

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class SelectorTester:
    """Test different CSS selectors on Europages to find working ones"""
    
    def __init__(self):
        self.engine = WebScrapingEngine(use_selenium=True, headless=False)  # Non-headless for debugging
    
    def test_europages_selectors(self, url: str = "https://www.europages.co.uk/companies/wines.html") -> Dict:
        """
        Test various CSS selectors on Europages wine section
        """
        print(f"\n Testing selectors on: {url}")
        print("="*60)
        
        # Fetch the page
        soup = self.engine.get_page(url)
        if not soup:
            print(" Failed to load page!")
            return {}
        
        # Save HTML for manual inspection
        with open('europages_debug.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"📄 Page HTML saved as 'europages_debug.html' for manual inspection")
        
        # Comprehensive list of selectors to test
        selectors = {
            # Original selector from your code
            'original': 'a[href*="/companies/"][href*=".html"]:not([href*="pg-"])',
            
            # Common patterns for business directories
            'company_title': 'a.company-title, .company-title a',
            'company_name': '.company-name a, a.company-name',
            'business_name': '.business-name a, a.business-name',
            'listing_title': '.listing-title a, a.listing-title',
            
            # Result-based selectors
            'search_results': '.search-result a[href*="/companies/"], .result-item a[href*="/companies/"]',
            'result_links': '.result a[href*="/companies/"], .results a[href*="/companies/"]',
            
            # Card-based selectors
            'card_title': '.card-title a, a.card-title',
            'card_header': '.card-header a, .card h3 a, .card h2 a',
            'card_link': '.card a[href*="/companies/"]',
            
            # Generic company link patterns
            'all_company_links': 'a[href*="/companies/"]',
            'html_company_links': 'a[href*="/companies/"][href$=".html"]',
            'europages_companies': 'a[href^="https://www.europages.co.uk/companies/"]',
            
            # Main content area
            'main_links': 'main a[href*="/companies/"], #main a[href*="/companies/"]',
            'content_links': '.content a[href*="/companies/"], #content a[href*="/companies/"]',
            
            # List-based selectors
            'list_item_links': 'li a[href*="/companies/"], .list-item a[href*="/companies/"]',
            'listing_links': '.listing a[href*="/companies/"], .listings a[href*="/companies/"]',
            
            # Data attribute selectors
            'data_company': '[data-company] a, a[data-company]',
            'data_business': '[data-business] a, a[data-business]',
            
            # Flexible patterns
            'h_tag_links': 'h1 a[href*="/companies/"], h2 a[href*="/companies/"], h3 a[href*="/companies/"]',
            'div_company_links': 'div a[href*="/companies/"][href*=".html"]'
        }
        
        results = {}
        
        for name, selector in selectors.items():
            try:
                elements = soup.select(selector)
                count = len(elements)
                results[name] = {
                    'count': count,
                    'selector': selector,
                    'examples': []
                }
                
                status = "FOUND" if count > 0 else "❌ EMPTY"
                print(f"\n{status} | {name:20} | {count:3d} links | {selector}")
                
                # Collect examples
                if elements:
                    for i, elem in enumerate(elements[:3]):  # First 3 examples
                        name_text = elem.get_text(strip=True)[:40]
                        href = elem.get('href', '')
                        
                        # Validate it's actually a company profile URL
                        if '/companies/' in href and href.endswith('.html') and 'pg-' not in href:
                            results[name]['examples'].append({
                                'text': name_text,
                                'url': href
                            })
                            print(f"    Example {i+1}: '{name_text}' -> {href[:60]}...")
                        
            except Exception as e:
                print(f"❌ ERROR | {name:20} | Selector error: {e}")
                results[name] = {'count': -1, 'error': str(e)}
        
        # Find best selectors
        valid_selectors = {k: v for k, v in results.items() 
                          if v.get('count', 0) > 0 and len(v.get('examples', [])) > 0}
        
        if valid_selectors:
            best = max(valid_selectors.items(), key=lambda x: x[1]['count'])
            print(f"\n BEST SELECTOR: '{best[0]}' found {best[1]['count']} valid company links")
            print(f"   Selector: {best[1]['selector']}")
        else:
            print(f"\n No valid selectors found! The page structure may have changed.")
        
        # Save detailed results
        with open('selector_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n Detailed results saved to 'selector_test_results.json'")
        
        return results
    
    def analyze_page_structure(self, url: str) -> None:
        """
        Analyze the page structure to understand how companies are organized
        """
        print(f"\n Analyzing page structure: {url}")
        print("="*60)
        
        soup = self.engine.get_page(url)
        if not soup:
            return
        
        # Look for common container patterns
        containers = [
            'div[class*="company"]',
            'div[class*="business"]', 
            'div[class*="result"]',
            'div[class*="listing"]',
            'div[class*="card"]',
            '.search-results, .results, .listings',
            'main, #main, .main-content, .content'
        ]
        
        print("📋 Container analysis:")
        for container_selector in containers:
            elements = soup.select(container_selector)
            if elements:
                print(f"   {container_selector}: {len(elements)} elements")
                
                # Look for links within these containers
                for container in elements[:2]:  # First 2 containers
                    links = container.select('a[href*="/companies/"]')
                    if links:
                        print(f"     → Contains {len(links)} company links")
            else:
                print(f"   {container_selector}: Not found")
        
        # Look for pagination
        print(f"\nPagination analysis:")
        pagination_selectors = [
            '.pagination', '.pager', '.page-nav',
            'a[href*="pg-"]', 'a[href*="page"]',
            '.next', '.next-page', '[rel="next"]'
        ]
        
        for pag_sel in pagination_selectors:
            elements = soup.select(pag_sel)
            if elements:
                print(f"  {pag_sel}: {len(elements)} elements")
    
    def test_multiple_urls(self) -> None:
        """Test selectors on multiple wine-related Europages URLs"""
        urls = [
            "https://www.europages.co.uk/companies/wines.html",
            "https://www.europages.co.uk/companies/wine%20producers.html", 
            "https://www.europages.co.uk/companies/french%20wine.html"
        ]
        
        all_results = {}
        
        for url in urls:
            print(f"\n{'='*80}")
            print(f"Testing URL: {url}")
            print('='*80)
            
            try:
                results = self.test_europages_selectors(url)
                all_results[url] = results
                
                # Brief pause between URLs
                import time
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Failed to test {url}: {e}")
        
        # Save comprehensive results
        with open('comprehensive_selector_test.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"\n💾 Comprehensive results saved to 'comprehensive_selector_test.json'")
    
    def __del__(self):
        """Cleanup"""
        if hasattr(self, 'engine') and self.engine.driver:
            self.engine.driver.quit()


def main():
    """Run the selector testing"""
    tester = SelectorTester()
    
    print("🚀 Europages Selector Testing Tool")
    print("="*50)
    
    try:
        # Test single URL first
        print("\n1️⃣ Testing main wines page...")
        tester.test_europages_selectors()
        
        # Analyze page structure
        print("\n2️⃣ Analyzing page structure...")
        tester.analyze_page_structure("https://www.europages.co.uk/companies/wines.html")
        
        # Test multiple URLs
        choice = input("\n❓ Test multiple wine URLs? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            print("\n3️⃣ Testing multiple URLs...")
            tester.test_multiple_urls()
        
        print("\n✅ Testing complete! Check the generated files:")
        print("   - europages_debug.html (page source)")
        print("   - selector_test_results.json (detailed results)")
        
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Testing failed: {e}")
    finally:
        # Cleanup
        del tester


if __name__ == "__main__":
    main()