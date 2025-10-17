# scripts/1_collect_links.py

import json
import os
import sys
import time
from sqlalchemy.orm import Session

# Add project root to the Python path to allow importing from 'src'
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.fls_analyzer import db_handler, scraper

# --- Configuration ---
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
EVENT_CONFIGS = {
    "UCL 2025": os.path.join(CONFIG_DIR, 'aggregators_uefa.json'),
    "NHL Stanley Cup 2025": os.path.join(CONFIG_DIR, 'aggregators_nhl.json'),
}
COLLECTION_INTERVAL_MINS = 15


def load_config(config_path: str) -> list:
    """Loads aggregator URLs from a JSON config."""
    try:
        with open(config_path, 'r') as f:
            return json.load(f).get('sites', [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading config {config_path}: {e}")
        return []

def process_aggregator(session: Session, agg_url: str, event_obj: db_handler.Event):
    """Scrapes a single aggregator and saves new links to the DB."""
    print(f"  Scraping {agg_url}...")
    
    # Check if aggregator is already in the DB, if not, create it
    agg_obj = session.query(db_handler.Aggregator).filter_by(url=agg_url).first()
    if not agg_obj:
        agg_obj = db_handler.Aggregator(url=agg_url, event=event_obj)
        session.add(agg_obj)
        session.flush() # Flush to assign an ID before committing

    new_links = scraper.scrape_links_from_url(agg_url)
    if not new_links:
        return

    # Check which links are genuinely new
    existing_urls = {res[0] for res in session.query(db_handler.ScrapedURL.url).filter(db_handler.ScrapedURL.url.in_(new_links)).all()}
    
    new_urls_to_add = []
    for link in new_links:
        if link not in existing_urls:
            new_urls_to_add.append(
                db_handler.ScrapedURL(
                    url=link,
                    event_id=event_obj.id,
                    aggregator_id=agg_obj.id
                )
            )

    if new_urls_to_add:
        session.bulk_save_objects(new_urls_to_add)
        session.commit()
        print(f"    -> Stored {len(new_urls_to_add)} new links in DB.")
    else:
        print("    -> No new links found.")


def main():
    """Main execution loop for the data collection script."""
    print("--- FLS Link Collector Initializing ---")
    
    # Ensure database exists before starting
    if not os.path.exists(db_handler.DB_PATH):
        print("Database not found. Running init_db()...")
        db_handler.init_db()

    session = db_handler.get_session()

    try:
        while True:
            print(f"\n--- Starting Collection Cycle ({time.ctime()}) ---")
            for event_name, config_path in EVENT_CONFIGS.items():
                print(f"[*] Processing event: {event_name}")
                
                event_obj = session.query(db_handler.Event).filter_by(name=event_name).first()
                if not event_obj:
                    print(f"  [!] Event '{event_name}' not in DB. Skipping.")
                    continue
                
                aggregator_list = load_config(config_path)
                for agg_url in aggregator_list:
                    process_aggregator(session, agg_url, event_obj)
            
            print(f"\n--- Cycle Complete. Sleeping for {COLLECTION_INTERVAL_MINS} minutes. ---")
            time.sleep(COLLECTION_INTERVAL_MINS * 60)

    except KeyboardInterrupt:
        print("\n[!] Shutdown signal received. Exiting gracefully.")
    finally:
        session.close()
        print("[*] Database session closed.")


if __name__ == "__main__":
    main()
