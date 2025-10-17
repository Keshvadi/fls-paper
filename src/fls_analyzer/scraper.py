# src/fls_analyzer/scraper.py

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import tldextract

# Domains to ignore when scraping for FLS links
DOMAIN_BLOCKLIST = [
    'facebook.com', 'twitter.com', 'instagram.com', 'youtube.com',
    'google.com', 'googletagmanager.com', 'doubleclick.net', 'amazon.com',
    'discord.gg', 'reddit.com', 't.me', 'dailymotion.com'
]

def _setup_driver():
    """Configures the selenium webdriver."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error setting up chromedriver: {e}")
        return None
    return driver

def scrape_links_from_url(agg_url: str) -> set:
    """
    Visits an aggregator URL and extracts potential FLS links.

    Args:
        agg_url: The URL of the aggregator website.

    Returns:
        A set of unique FLS URLs found on the page.
    """
    driver = _setup_driver()
    if not driver:
        return set()

    found_urls = set()
    agg_domain = tldextract.extract(agg_url).registered_domain

    try:
        driver.get(agg_url)
        
        # TODO: Replace this with an explicit wait for better performance
        # For now, a fixed sleep is simple and works for most JS-heavy sites.
        # don't send many requests to the same site in a short time. especially during the test. 
        time.sleep(7) 
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href'].strip()
            
            if not link or not link.startswith('http'):
                continue

            link_domain_info = tldextract.extract(link)
            link_domain = link_domain_info.registered_domain
            
            if link_domain and link_domain != agg_domain and link_domain not in DOMAIN_BLOCKLIST:
                found_urls.add(link)
                
    except Exception as e:
        print(f"Error scraping {agg_url}: {e}")
    finally:
        driver.quit()
        
    return found_urls


if __name__ == '__main__':
    # For direct testing of this module
    test_url = "http://onhockey.tv" 
    print(f"Running a test scrape on: {test_url}")
    
    links = scrape_links_from_url(test_url)
    
    if links:
        print(f"Found {len(links)} links:")
        for l in list(links)[:15]:
            print(f"  - {l}")
    else:
        print("No valid links were found.")
