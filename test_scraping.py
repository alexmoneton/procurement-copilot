#!/usr/bin/env python3
"""
Test script to trigger data scraping via API calls to our Railway deployment.
"""

import requests
import json
import time

BASE_URL = "https://procurement-copilot-production.up.railway.app"

def test_health():
    """Test basic API health."""
    print("🔍 Testing API health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def test_db_health():
    """Test database connection."""
    print("\n🔍 Testing database health...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"DB Health Status: {response.status_code}")
    print(f"Response: {response.json()}")
    return response.status_code == 200

def check_tenders():
    """Check existing tenders in database."""
    print("\n📊 Checking existing tenders...")
    try:
        # Test tenders endpoint
        response = requests.get(f"{BASE_URL}/api/v1/tenders/tenders?limit=5")
        print(f"Tenders Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Found {data['total']} total tenders (showing {len(data['items'])})")
            if data['items']:
                for tender in data['items'][:3]:
                    value_str = f"{tender.get('value_amount', 'N/A')} {tender.get('currency', '')}"
                    print(f"  • {tender['tender_ref']}: {tender['title'][:40]}... ({tender['source']}, {value_str})")
        else:
            print(f"Response: {response.text}")
            
        # Test stats endpoint
        print("\n📈 Checking tender statistics...")
        stats_response = requests.get(f"{BASE_URL}/api/v1/tenders/tenders/stats/summary")
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"Total Tenders: {stats['total_tenders']}")
            print(f"By Source: {stats['by_source']}")
            print(f"Top Countries: {stats['top_countries']}")
            print(f"Recent (7 days): {stats['recent_tenders_7_days']}")
        
        # Test search functionality
        print("\n🔍 Testing search functionality...")
        search_response = requests.get(f"{BASE_URL}/api/v1/tenders/tenders?query=construction&limit=3")
        if search_response.status_code == 200:
            search_data = search_response.json()
            print(f"Construction search results: {search_data['total']} matches")
            for tender in search_data['items']:
                print(f"  • {tender['title'][:50]}... ({tender['buyer_country']})")
                
    except Exception as e:
        print(f"Error checking tenders: {e}")

def main():
    """Run all tests."""
    print("🚀 Starting Procurement Copilot Data Pipeline Test")
    print("=" * 50)
    
    # Test API health
    if not test_health():
        print("❌ API health check failed")
        return
    
    # Test database health  
    if not test_db_health():
        print("❌ Database health check failed")
        return
    
    print("✅ All health checks passed!")
    
    # Check existing data
    check_tenders()
    
    print("\n🎉 Test completed successfully!")
    print("🔗 Frontend: https://procurement-copilot-frontend.vercel.app")
    print("🔗 Backend: https://procurement-copilot-production.up.railway.app")

if __name__ == "__main__":
    main()
