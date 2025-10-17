# scripts/2_analyze_threats.py

import os
import sys
import time
from sqlalchemy.orm import Session, subqueryload

# Add project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.fls_analyzer import db_handler, security_analysis

# VirusTotal public API allows 4 requests/min. 16s sleep gives a small buffer.
VT_API_RATE_LIMIT_SLEEP = 16 

def get_urls_needing_analysis(session: Session, limit: int = 100):
    """
    Fetches a batch of URLs from the DB that haven't been analyzed yet.
    """
    # Find ScrapedURL objects where a corresponding SecurityAnalysis record does not exist.
    urls = (
        session.query(db_handler.ScrapedURL)
        .outerjoin(db_handler.SecurityAnalysis)
        .filter(db_handler.SecurityAnalysis.id == None)
        .limit(limit)
        .all()
    )
    return urls

def main():
    """
    Main execution script to analyze URLs for security threats.
    """
    print("--- FLS Security Threat Analyzer ---")
    session = db_handler.get_session()

    try:
        while True:
            urls_to_process = get_urls_needing_analysis(session, limit=50) # Process in batches of 50
            
            if not urls_to_process:
                print("No new URLs to analyze. Waiting...")
                time.sleep(60)
                continue

            print(f"Found {len(urls_to_process)} URLs to analyze...")

            for url_obj in urls_to_process:
                print(f"[*] Analyzing: {url_obj.url}")
                
                # Get the VirusTotal report
                vt_report = security_analysis.get_virustotal_report(url_obj.url)

                analysis_record = db_handler.SecurityAnalysis(url_id=url_obj.id)

                if "error" in vt_report:
                    print(f"  [!] VT Error: {vt_report['error']}")
                    # Still save a record so we don't try this URL again
                    analysis_record.vt_score = -1 
                else:
                    # 'malicious' is a key in the VT stats dictionary
                    malicious_count = vt_report.get('malicious', 0)
                    analysis_record.vt_score = malicious_count
                    print(f"  > VT Score: {malicious_count} malicious vendors.")
                
                # TODO: Add logic here to check for drive-by-downloads
                # and pass the file to the cuckoo analysis function.
                # For now, we'll just create the security record.

                session.add(analysis_record)
                session.commit()
                
                # Respect API rate limits. For testing, we can reduce this to 1 second.
                time.sleep(VT_API_RATE_LIMIT_SLEEP)

    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received.")
    finally:
        session.close()
        print("[*] Analysis complete. Database session closed.")


if __name__ == "__main__":
    main()
