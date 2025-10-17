# src/fls_analyzer/security_analysis.py

import os
import requests
import time
from dotenv import load_dotenv

# Load API keys from .env file for security
load_dotenv()
# TODO: import this key from a .env file when you're done with testing
VT_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")

VT_URL_SCAN_ENDPOINT = 'https://www.virustotal.com/api/v3/urls'
VT_URL_ANALYSIS_ENDPOINT = 'https://www.virustotal.com/api/v3/analyses/{}'


def get_virustotal_report(url_to_scan: str) -> dict:
    if not VT_API_KEY:
        return {"error": "VirusTotal API key not found. Please set VIRUSTOTAL_API_KEY in .env file."}

    headers = {'x-apikey': VT_API_KEY}
    
    # Submit the URL for scanning
    try:
        scan_payload = {'url': url_to_scan}
        response = requests.post(VT_URL_SCAN_ENDPOINT, data=scan_payload, headers=headers)
        response.raise_for_status()
        analysis_id = response.json()['data']['id']
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to submit URL to VirusTotal: {e}"}

    # Wait for the analysis to complete. This can be slow.
    print(f"  > VT: Submitted {url_to_scan}. Waiting for analysis...")
    analysis_url = VT_URL_ANALYSIS_ENDPOINT.format(analysis_id)
    
    # Polling for results
    for _ in range(10): # Poll up to 10 times (e.g., 2 minutes)
        try:
            time.sleep(15) # Wait 15 seconds between checks
            analysis_response = requests.get(analysis_url, headers=headers)
            analysis_response.raise_for_status()
            result = analysis_response.json()

            if result['data']['attributes']['status'] == 'completed':
                print("  > VT: Analysis complete.")
                return result['data']['attributes']['stats']
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to retrieve VT analysis: {e}"}

    return {"error": "VirusTotal analysis timed out."}


def analyze_in_cuckoo(file_path: str) -> dict:
    """
    Placeholder function to simulate submitting a file to Cuckoo Sandbox.
    
    In a real implementation, this would involve using the Cuckoo API
    to submit the file and retrieve a report ID.
    """
    print(f"\n[CUCKOO] Submitting {os.path.basename(file_path)} for analysis...")
    print("[CUCKOO] Analysis complete (simulated).")
    return {
        "summary": {
            "file_name": os.path.basename(file_path),
            "persistence_methods": ["Registry Run Key (HKCU)"],
            "network_activity": {
                "dns_requests": ["updates.topcreativeformat.com", "badsite.ru"],
                "http_posts_to": ["http://updates.topcreativeformat.com/report"]
            },
            "files_created": ["%AppData%\\Roaming\\SysUtil\\updater.exe"]
        },
        "report_path": f"/path/to/cuckoo/reports/{os.path.basename(file_path)}.json"
    }


if __name__ == '__main__':
    # --- Test for VirusTotal ---
    test_url_vt = "http://www.google.com/" # A safe URL for testing
    print(f"--- Testing VirusTotal analysis for: {test_url_vt} ---")
    vt_results = get_virustotal_report(test_url_vt)
    print("VT Results:", vt_results)
    
    # --- Test for Cuckoo ---
    dummy_file = "HD-Player-update.exe"
    with open(dummy_file, "w") as f:
        f.write("test malware content")
        
    print(f"\n--- Testing Cuckoo analysis for: {dummy_file} ---")
    cuckoo_results = analyze_in_cuckoo(dummy_file)
    print("Cuckoo Results:", json.dumps(cuckoo_results, indent=2))
    
    os.remove(dummy_file)
