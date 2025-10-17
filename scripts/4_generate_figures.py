# scripts/4_generate_figures.py

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import func

# Add project root to the Python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from src.fls_analyzer import db_handler

# --- Configuration ---
FIGURES_DIR = os.path.join(PROJECT_ROOT, 'figures')
os.makedirs(FIGURES_DIR, exist_ok=True)


def load_data_into_dataframe():
    """Loads all relevant data from the database into a pandas DataFrame."""
    session = db_handler.get_session()
    
    # Query to join all tables together
    query = (
        session.query(
            db_handler.ScrapedURL.url,
            db_handler.Event.name.label('event_name'),
            db_handler.SecurityAnalysis.vt_score,
            db_handler.SecurityAnalysis.is_phishing,
            db_handler.SecurityAnalysis.drive_by_download_detected,
            db_handler.PrivacyAnalysis.vp_analysis_data
        )
        .join(db_handler.Event)
        .outerjoin(db_handler.SecurityAnalysis)
        .outerjoin(db_handler.PrivacyAnalysis)
    )
    
    df = pd.read_sql(query.statement, session.bind)
    session.close()
    return df


def generate_threat_prevalence_table(df):
    """Generates and prints the Threat Prevalence table (Table I)."""
    print("\n--- Generating Threat Prevalence Table (Table I) ---")
    
    prevalence = df.groupby('event_name').agg(
        Total_URLs=('url', 'count'),
        Drive_by_Downloads=('drive_by_download_detected', lambda x: x.sum() / len(x) * 100),
        Malicious_JS=('vt_score', lambda x: (x > 5).sum() / len(x) * 100), # Example: >5 vendors
        Phishing=('is_phishing', lambda x: x.sum() / len(x) * 100)
    ).round(1)
    
    print(prevalence)


def generate_comparative_threat_barchart(df):
    """Generates a bar chart comparing threat types across events."""
    print("\n--- Generating Comparative Threat Bar Chart ---")
    
    data_for_plot = df.groupby('event_name').agg(
        Drive_by_Downloads=('drive_by_download_detected', 'mean'),
        Phishing=('is_phishing', 'mean'),
        Malicious_JS=('vt_score', lambda x: (x > 5).mean())
    ).reset_index()
    
    melted_df = data_for_plot.melt(id_vars='event_name', var_name='Threat Type', value_name='Prevalence')
    melted_df['Prevalence'] *= 100 # To percentage

    plt.figure(figsize=(10, 6))
    sns.barplot(data=melted_df, x='Threat Type', y='Prevalence', hue='event_name')
    plt.title('Comparative Threat Prevalence Across FLS Events')
    plt.ylabel('Prevalence (%)')
    plt.xlabel('Threat Type')
    plt.tight_layout()
    
    output_path = os.path.join(FIGURES_DIR, 'fig_threat_comparison.png')
    plt.savefig(output_path)
    print(f"[*] Chart saved to {output_path}")
    plt.close()


def generate_privacy_table(df):
    """Generates the privacy analysis table (Table II)."""
    print("\n--- Generating Privacy Analysis Table (Table II) - Placeholder ---")
    # todo - generate a table based on the JSON data not your current customized script


def main():
    """Main function to load data and generate all paper figures."""
    print("--- Figure Generation Script ---")
    
    df = load_data_into_dataframe()
    if df.empty:
        print("[!] Database is empty or no analyzed data found. Exiting.")
        return
        
    generate_threat_prevalence_table(df)
    generate_comparative_threat_barchart(df)
    generate_privacy_table(df)

    print("\n--- All figures generated successfully. ---")


if __name__ == "__main__":
    main()
