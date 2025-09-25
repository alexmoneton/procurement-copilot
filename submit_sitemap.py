
# Sitemap Submission Script
# Run this after setting up Google Search Console API

import requests
import json

def submit_sitemap():
    # You'll need to set up Google Search Console API credentials
    # and get an access token
    
    sitemap_url = "https://tenderpulse.eu/sitemap.xml"
    
    # This is a placeholder - you'll need to implement OAuth2 flow
    # for Google Search Console API
    
    print(f"Submitting sitemap: {sitemap_url}")
    print("Note: This requires Google Search Console API setup")
    print("For now, submit manually via the web interface")

if __name__ == "__main__":
    submit_sitemap()
