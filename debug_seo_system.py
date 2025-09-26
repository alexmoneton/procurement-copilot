#!/usr/bin/env python3
"""
Debug the SEO system to see what's in the database
"""

import requests
import json

def main():
    print("🔍 DEBUGGING SEO SYSTEM DATABASE")
    print("="*60)
    
    base_url = "https://api.tenderpulse.eu"
    
    try:
        # Check cluster status
        print("\\n📊 Checking cluster status...")
        response = requests.get(f"{base_url}/api/v1/admin/cluster-status")
        
        if response.status_code == 200:
            clusters = response.json()
            for cluster in clusters:
                print(f"\\n🏢 Cluster: {cluster['cluster']['slug']}")
                print(f"   Status: {cluster['cluster']['status']}")
                print(f"   Target Daily: {cluster['cluster']['target_daily']}")
                print(f"   Threshold: {cluster['cluster']['threshold_pct']}%")
                print(f"   Total Pages: {cluster['pages']['total']}")
                print(f"   Submitted: {cluster['pages']['submitted']}")
                print(f"   Indexed: {cluster['pages']['indexed']}")
                print(f"   Quality OK: {cluster['pages']['quality_ok']}")
                print(f"   Ready to Publish: {cluster['pages']['ready_to_publish']}")
                print(f"   Coverage: {cluster['metrics']['coverage_pct']}%")
        else:
            print(f"❌ Failed to get cluster status: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
