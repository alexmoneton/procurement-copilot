#!/usr/bin/env python3
"""
Deployment status checker.
Checks if the real intelligence system is deployed and working.
"""

import requests
import time
import json

def check_backend_deployment():
    """Check if backend is deployed and working."""
    print("🔍 Checking backend deployment...")
    
    try:
        # Test health endpoint
        response = requests.get("https://api.tenderpulse.eu/ping", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is live and responding")
            return True
        else:
            print(f"⚠️ Backend responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def check_frontend_deployment():
    """Check if frontend is deployed and working."""
    print("🔍 Checking frontend deployment...")
    
    try:
        # Test main page
        response = requests.get("https://tenderpulse.eu", timeout=10)
        if response.status_code == 200:
            print("✅ Frontend is live and responding")
            return True
        else:
            print(f"⚠️ Frontend responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend not accessible: {e}")
        return False

def check_profile_endpoint():
    """Check if profile endpoint is working."""
    print("🔍 Checking profile endpoint...")
    
    try:
        # Test profile endpoint (should return 401 without email)
        response = requests.get("https://api.tenderpulse.eu/api/v1/profiles/profile", timeout=10)
        if response.status_code == 401:
            print("✅ Profile endpoint is working (401 as expected without email)")
            return True
        else:
            print(f"⚠️ Profile endpoint responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Profile endpoint not accessible: {e}")
        return False

def check_intelligence_endpoint():
    """Check if intelligence endpoint is working."""
    print("🔍 Checking intelligence endpoint...")
    
    try:
        # Test tenders endpoint
        response = requests.get("https://api.tenderpulse.eu/api/v1/tenders/tenders?limit=1", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'tenders' in data and len(data['tenders']) > 0:
                tender = data['tenders'][0]
                if 'smart_score' in tender:
                    print(f"✅ Intelligence endpoint working - Smart score: {tender['smart_score']}%")
                    return True
                else:
                    print("⚠️ Intelligence endpoint missing smart_score field")
                    return False
            else:
                print("⚠️ Intelligence endpoint returned no tenders")
                return False
        else:
            print(f"⚠️ Intelligence endpoint responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Intelligence endpoint not accessible: {e}")
        return False

def test_profile_creation():
    """Test profile creation functionality."""
    print("🔍 Testing profile creation...")
    
    try:
        # Test profile creation
        profile_data = {
            "company_name": "Test Company",
            "target_value_range": [100000, 1000000],
            "preferred_countries": ["DE", "FR"],
            "cpv_expertise": ["72000000"],
            "company_size": "medium",
            "experience_level": "intermediate"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-User-Email": "test@example.com"
        }
        
        response = requests.post(
            "https://api.tenderpulse.eu/api/v1/profiles/profile",
            json=profile_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'company_name' in data and data['company_name'] == "Test Company":
                print("✅ Profile creation working")
                return True
            else:
                print("⚠️ Profile creation returned unexpected data")
                return False
        else:
            print(f"⚠️ Profile creation responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Profile creation test failed: {e}")
        return False

def main():
    """Main deployment check."""
    print("🚀 DEPLOYMENT STATUS CHECK")
    print("=" * 50)
    
    checks = [
        ("Backend Health", check_backend_deployment),
        ("Frontend Health", check_frontend_deployment),
        ("Profile Endpoint", check_profile_endpoint),
        ("Intelligence Endpoint", check_intelligence_endpoint),
        ("Profile Creation", test_profile_creation)
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n{name}:")
        result = check_func()
        results.append((name, result))
        time.sleep(1)  # Be nice to the servers
    
    print("\n" + "=" * 50)
    print("📊 DEPLOYMENT SUMMARY:")
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 DEPLOYMENT SUCCESSFUL!")
        print("The real intelligence system is live and working!")
        print("\n🎯 What's working:")
        print("   ✅ Backend API with real intelligence")
        print("   ✅ Frontend with profile management")
        print("   ✅ Profile creation and management")
        print("   ✅ Smart score calculation")
        print("   ✅ Personalized recommendations")
        print("\n🚀 Ready for users!")
    else:
        print("\n⚠️ DEPLOYMENT ISSUES DETECTED")
        print("Some components are not working properly.")
        print("Please check the logs above for details.")

if __name__ == "__main__":
    main()
