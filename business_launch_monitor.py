#!/usr/bin/env python3
"""
Business Launch Monitor - Comprehensive System Health Check
Tracks all critical systems for revenue generation
"""

import requests
import json
import asyncio
import sys
from datetime import datetime
from typing import Dict, Any, List
import os

class BusinessLaunchMonitor:
    def __init__(self):
        self.base_url = "https://api.tenderpulse.eu"
        self.frontend_url = "https://tenderpulse.eu"
        self.results = {}
        
    def check_stripe_payments(self) -> Dict[str, Any]:
        """Check Stripe payment system"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/billing/test", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "OPERATIONAL",
                    "stripe_available": data.get("stripe_available", False),
                    "stripe_configured": data.get("stripe_configured", False),
                    "db_available": data.get("db_available", False)
                }
            else:
                return {"status": "ERROR", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def check_frontend(self) -> Dict[str, Any]:
        """Check frontend availability"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                return {"status": "OPERATIONAL", "response_time": response.elapsed.total_seconds()}
            else:
                return {"status": "ERROR", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def check_app_pages(self) -> Dict[str, Any]:
        """Check critical app pages"""
        pages = {
            "app": f"{self.frontend_url}/app",
            "pricing": f"{self.frontend_url}/pricing",
            "signup": f"{self.frontend_url}/sign-up",
            "signin": f"{self.frontend_url}/sign-in"
        }
        
        results = {}
        for name, url in pages.items():
            try:
                response = requests.get(url, timeout=10)
                results[name] = {
                    "status": "OPERATIONAL" if response.status_code == 200 else "ERROR",
                    "status_code": response.status_code
                }
            except Exception as e:
                results[name] = {"status": "ERROR", "error": str(e)}
        
        return results
    
    def check_email_system(self) -> Dict[str, Any]:
        """Check email system"""
        try:
            # Test email endpoint
            response = requests.post(
                f"{self.base_url}/api/v1/admin/test-email",
                params={
                    "to": "test@tenderpulse.eu",
                    "subject": "Health Check Test",
                    "message": "System health check - automated test"
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "OPERATIONAL",
                    "email_id": data.get("result", {}).get("id", "unknown")
                }
            else:
                return {"status": "ERROR", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def check_prospect_pipeline(self) -> Dict[str, Any]:
        """Check prospect pipeline"""
        try:
            # Import and test the prospect finder
            sys.path.append('.')
            from advanced_ted_prospect_finder import TEDProspectFinder, ConfigManager
            
            config = ConfigManager()
            finder = TEDProspectFinder(config)
            
            return {
                "status": "OPERATIONAL",
                "config_loaded": True,
                "finder_initialized": True
            }
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    def run_comprehensive_check(self) -> Dict[str, Any]:
        """Run all health checks"""
        print("🔍 Running Business Launch Health Checks...")
        
        checks = {
            "stripe_payments": self.check_stripe_payments(),
            "frontend": self.check_frontend(),
            "app_pages": self.check_app_pages(),
            "email_system": self.check_email_system(),
            "prospect_pipeline": self.check_prospect_pipeline()
        }
        
        # Calculate overall health
        operational_count = sum(1 for check in checks.values() 
                              if isinstance(check, dict) and check.get("status") == "OPERATIONAL")
        total_checks = len(checks)
        health_score = (operational_count / total_checks) * 100
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_health_score": health_score,
            "operational_systems": operational_count,
            "total_systems": total_checks,
            "checks": checks,
            "launch_ready": health_score >= 80
        }
        
        return results
    
    def print_report(self, results: Dict[str, Any]):
        """Print formatted health report"""
        print("\n" + "="*60)
        print("🚀 TENDERPULSE BUSINESS LAUNCH HEALTH REPORT")
        print("="*60)
        print(f"📅 Timestamp: {results['timestamp']}")
        print(f"🏥 Overall Health Score: {results['overall_health_score']:.1f}%")
        print(f"✅ Operational Systems: {results['operational_systems']}/{results['total_systems']}")
        print(f"🚀 Launch Ready: {'YES' if results['launch_ready'] else 'NO'}")
        print("\n" + "-"*60)
        
        for system, check in results['checks'].items():
            status_icon = "✅" if check.get("status") == "OPERATIONAL" else "❌"
            print(f"{status_icon} {system.upper().replace('_', ' ')}: {check.get('status', 'UNKNOWN')}")
            
            if check.get("status") != "OPERATIONAL":
                print(f"   ⚠️  Error: {check.get('error', 'Unknown error')}")
        
        print("\n" + "="*60)
        
        if results['launch_ready']:
            print("🎉 BUSINESS LAUNCH: READY TO GO!")
            print("💰 Revenue generation systems are operational")
            print("📧 Customer acquisition pipeline is ready")
            print("💳 Payment processing is working")
        else:
            print("⚠️  BUSINESS LAUNCH: NOT READY")
            print("🔧 Fix the issues above before launching")
        
        print("="*60)
    
    def save_report(self, results: Dict[str, Any]):
        """Save report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"business_launch_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Report saved to: {filename}")

def main():
    monitor = BusinessLaunchMonitor()
    results = monitor.run_comprehensive_check()
    monitor.print_report(results)
    monitor.save_report(results)
    
    # Exit with appropriate code
    sys.exit(0 if results['launch_ready'] else 1)

if __name__ == "__main__":
    main()
