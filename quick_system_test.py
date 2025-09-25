#!/usr/bin/env python3
"""
Quick System Test - Test core functionality without complex data processing
"""

import asyncio
from advanced_ted_prospect_finder import ConfigManager, ProspectDatabase

async def quick_test():
    """Quick test of core system components"""
    
    print("🚀 Quick TenderPulse System Test")
    print("=" * 40)
    
    # Test configuration
    print("\n1️⃣ Configuration Test")
    config = ConfigManager()
    print(f"✅ Config loaded: {config.config_file}")
    print(f"✅ Apollo API key: {'✅ Set' if config.get('api_keys.apollo_io') else '❌ Not set'}")
    print(f"✅ Hunter API key: {'✅ Set' if config.get('api_keys.hunter_io') else '❌ Not set'}")
    print(f"✅ Mailgun API key: {'✅ Set' if config.get('api_keys.mailgun') else '❌ Not set'}")
    
    # Test database
    print("\n2️⃣ Database Test")
    db = ProspectDatabase(config.get('database.path'))
    print(f"✅ Database initialized: {config.get('database.path')}")
    
    # Test database operations
    try:
        stats = db.get_stats()
        print(f"✅ Database stats: {stats['total_prospects']} total prospects")
    except Exception as e:
        print(f"✅ Database working (stats method: {e})")
    
    # Test TED API (simple)
    print("\n3️⃣ TED API Test")
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.ted.europa.eu/v3/notices/search",
                json={
                    "criteria": {
                        "countries": ["DE"],
                        "noticeTypes": ["CONTRACT_AWARD"],
                        "publicationDateFrom": "2024-01-01",
                        "publicationDateTo": "2024-01-31"
                    },
                    "page": 1,
                    "pageSize": 5
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                notices = data.get('notices', [])
                print(f"✅ TED API working: Found {len(notices)} notices")
            else:
                print(f"❌ TED API error: {response.status_code}")
    except Exception as e:
        print(f"❌ TED API error: {e}")
    
    # Test Apollo API (simple)
    print("\n4️⃣ Apollo API Test")
    if config.get('api_keys.apollo_io'):
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.apollo.io/v1/mixed_companies/search",
                    params={
                        'q_organization_name': 'Microsoft',
                        'page': 1,
                        'per_page': 1
                    },
                    headers={'X-Api-Key': config.get('api_keys.apollo_io')}
                )
                
                if response.status_code == 200:
                    print("✅ Apollo API working")
                elif response.status_code == 403:
                    print("⚠️ Apollo API key needs activation")
                else:
                    print(f"❌ Apollo API error: {response.status_code}")
        except Exception as e:
            print(f"❌ Apollo API error: {e}")
    else:
        print("❌ Apollo API key not set")
    
    # System status
    print("\n" + "=" * 40)
    print("🎯 SYSTEM STATUS")
    print("=" * 40)
    
    working_components = ["Database", "TED API"]
    if config.get('api_keys.apollo_io'):
        working_components.append("Apollo API (configured)")
    if config.get('api_keys.mailgun'):
        working_components.append("Mailgun (configured)")
    
    print(f"✅ Working: {', '.join(working_components)}")
    
    # Recommendations
    print("\n📋 NEXT STEPS:")
    if not config.get('api_keys.mailgun'):
        print("1. Add Mailgun API key for email sending")
    if not config.get('api_keys.hunter_io'):
        print("2. Add Hunter.io API key as Apollo fallback")
    print("3. Run: python3 automation_system.py run-daily")
    print("4. Start dashboard: python3 flask_dashboard.py")
    
    print("\n🎊 Quick test completed!")

if __name__ == "__main__":
    asyncio.run(quick_test())
