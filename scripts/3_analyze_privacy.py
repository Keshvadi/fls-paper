# scripts/3_analyze_privacy.py

import os
import sys
import time
import json
from sqlalchemy.orm import Session

# Add project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.fls_analyzer import db_handler, privacy_analysis, scraper

# --- Configuration ---
# For test just re-scraping from the same location. Don't use proxies. Use it for final data collection only.
# VANTAGE_POINTS = ["CA"] 
VANTAGE_POINTS = ["CA", "US", "DE", "SG"] 


def get_unprocessed_urls(session: Session, limit: int = 25):
    """Fetches URLs that do not have a privacy analysis record yet."""
    urls = (
        session.query(db_handler.ScrapedURL)
        .outerjoin(db_handler.PrivacyAnalysis)
        .filter(db_handler.PrivacyAnalysis.id == None)
        .limit(limit)
        .all()
    )
    return urls

def perform_vp_analysis(url: str):
    """
    Simulates scraping a URL from multiple vantage points and analyzes each result.
    """
    vp_results = {}
    for vp in VANTAGE_POINTS:
        print(f"    > Crawling from VP: {vp}...")
        # Here we simulate it by just re-scraping.
        page_source = scraper.scrape_links_from_url(url)
        
        # You might get slightly different content from each VP. Check this before running the data collection on stanly cup finals.
        page_source = f"<html><body><!-- VP: {vp} --> <script>var ua_code = 'UA-1111{VANTAGE_POINTS.index(vp)}-1';</script></body></html>"

        analysis = privacy_analysis.analyze_privacy_from_source(page_source)
        vp_results[vp] = analysis
        
    return vp_results


def aggregate_google_ids(vp_results: dict):
    """Extracts all unique Google IDs from the per-VP analysis results."""
    all_ids = set()
    for vp, data in vp_results.items():
        if "google_ids" in data:
            for id_type, id_list in data["google_ids"].items():
                for an_id in id_list:
                    all_ids.add(an_id)
    return list(all_ids)


def main():
    print("--- FLS Privacy Analyzer ---")
    session = db_handler.get_session()

    try:
        while True:
            urls_to_process = get_unprocessed_urls(session, limit=10)
            
            if not urls_to_process:
                print("No new URLs for privacy analysis. Waiting...")
                time.sleep(120)
                continue

            print(f"Found {len(urls_to_process)} URLs to analyze for privacy risks...")
            for url_obj in urls_to_process:
                print(f"[*] Processing: {url_obj.url}")
                
                # Perform the analysis from all VPs
                vp_analysis_data = perform_vp_analysis(url_obj.url)
                
                # Consolidate all found Google IDs into one list
                unique_google_ids = aggregate_google_ids(vp_analysis_data)
                
                # Create the database record
                privacy_record = db_handler.PrivacyAnalysis(
                    url_id=url_obj.id,
                    vp_analysis_data=vp_analysis_data,
                    google_publisher_ids=unique_google_ids
                )
                
                session.add(privacy_record)
                session.commit()
                print(f"  > Stored privacy analysis for {url_obj.url}")
                
                # Add a small delay between processing URLs
                time.sleep(5) 

    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received.")
    finally:
        session.close()
        print("[*] Database session closed.")


if __name__ == "__main__":
    main()

