# src/fls_analyzer/privacy_analysis.py

import re
from selenium import webdriver
from bs4 import BeautifulSoup

# Regex patterns for finding common Google tracking IDs
# TODO: Expand this to include other ad networks like Criteo, etc.
GOOGLE_ID_PATTERNS = {
    'GA_UA': re.compile(r'UA-\d{4,10}-\d{1,4}'),
    'GA_G': re.compile(r'G-[A-Z0-9]{10}'),
    'GTM': re.compile(r'GTM-[A-Z0-9]{7}'),
    'ADSENSE': re.compile(r'pub-\d{15,20}')
}

# Simple list of strings to look for in script content to detect fingerprinting
# This is a basic heuristic approach. A more advanced method would use JS instrumentation.
FINGERPRINTING_KEYWORDS = [
    'canvas.todataurl',
    'getclientrects',
    'navigatordetails', 
    'audiocontext',
    'getplugindata'
]


def _find_google_ids(page_source: str) -> dict:
    """Finds all Google publisher/tracking IDs in the page source."""
    found_ids = {}
    for id_type, pattern in GOOGLE_ID_PATTERNS.items():
        matches = pattern.findall(page_source)
        if matches:
            found_ids[id_type] = list(set(matches)) 
    return found_ids


def _detect_fingerprinting(page_source: str) -> list:
    """Detects potential fingerprinting techniques via keyword matching in scripts."""
    detected_techniques = []
    soup = BeautifulSoup(page_source, 'html.parser')
    scripts = soup.find_all('script')
    
    for script in scripts:
        script_content = str(script) 
        for keyword in FINGERPRINTING_KEYWORDS:
            if keyword.lower() in script_content.lower() and keyword not in detected_techniques:
                detected_techniques.append(keyword)

    return detected_techniques


def analyze_privacy_from_source(page_source: str) -> dict:
    """
    Analyzes a given HTML page source for privacy-related metrics.
    
    This function is designed to be called by a crawler that has already
    fetched the page source from a specific vantage point.
    
    Args:
        page_source: The HTML content of the page as a string.
        
    Returns:
        A dictionary containing the analysis results.
    """
    if not page_source:
        return {
            "error": "Empty page source provided."
        }
        
    google_ids = _find_google_ids(page_source)
    fingerprinting = _detect_fingerprinting(page_source)
    
    return {
        "google_ids": google_ids,
        "fingerprinting_techniques": fingerprinting,
    }


if __name__ == '__main__':
    # For direct testing of this module's functions
    # You would paste HTML source code here to test it.
    
    test_html = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <p>Some content here. Your ad client is pub-1234567890123456.</p>
            <script>
                var ua_code = 'UA-9876543-2';
                console.log("Analytics loaded");
                
                // FP detection example
                var canvas = document.createElement('canvas');
                var data = canvas.toDataURL('image/png');
            </script>
        </body>
    </html>
    """
    
    print("--- Testing Privacy Analysis Functions ---")
    privacy_results = analyze_privacy_from_source(test_html)
    
    import json
    print(json.dumps(privacy_results, indent=2))
