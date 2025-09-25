#!/usr/bin/env python3
"""
Simple SEO Status Checker for TenderPulse
Checks basic SEO functionality without external dependencies
"""

import urllib.request
import urllib.error
import json
from datetime import datetime
import time

class SimpleSEOChecker:
    """Simple SEO status checker"""
    
    def __init__(self, base_url: str = "https://tenderpulse.eu"):
        self.base_url = base_url
    
    def check_url(self, url: str, timeout: int = 10) -> dict:
        """Check if a URL is accessible"""
        try:
            start_time = time.time()
            response = urllib.request.urlopen(url, timeout=timeout)
            response_time = time.time() - start_time
            
            return {
                'status_code': response.getcode(),
                'response_time': round(response_time, 2),
                'accessible': True,
                'content_length': len(response.read()) if hasattr(response, 'read') else 0
            }
        except urllib.error.HTTPError as e:
            return {
                'status_code': e.code,
                'response_time': 0,
                'accessible': False,
                'error': f'HTTP {e.code}'
            }
        except urllib.error.URLError as e:
            return {
                'status_code': 0,
                'response_time': 0,
                'accessible': False,
                'error': str(e.reason)
            }
        except Exception as e:
            return {
                'status_code': 0,
                'response_time': 0,
                'accessible': False,
                'error': str(e)
            }
    
    def check_sitemap(self) -> dict:
        """Check sitemap status"""
        sitemap_url = f"{self.base_url}/sitemap.xml"
        result = self.check_url(sitemap_url)
        
        if result['accessible']:
            # Try to get content to count URLs
            try:
                response = urllib.request.urlopen(sitemap_url, timeout=10)
                content = response.read().decode('utf-8')
                url_count = content.count('<url>')
                result['url_count'] = url_count
            except:
                result['url_count'] = 0
        
        return result
    
    def check_seo_pages(self) -> dict:
        """Check key SEO pages"""
        pages = [
            "/seo/countries/de",
            "/seo/countries/fr", 
            "/seo/countries/es",
            "/seo/cpv-codes/72000000",
            "/seo/cpv-codes/45000000",
            "/seo/value-ranges/medium"
        ]
        
        results = {}
        for page in pages:
            url = f"{self.base_url}{page}"
            results[page] = self.check_url(url)
        
        return results
    
    def check_api_endpoints(self) -> dict:
        """Check API endpoints"""
        endpoints = [
            "/api/v1/seo/tenders",
            "/api/v1/seo/sitemap-data",
            "/api/v1/seo/page-intro"
        ]
        
        results = {}
        for endpoint in endpoints:
            url = f"{self.base_url}{endpoint}"
            results[endpoint] = self.check_url(url)
        
        return results
    
    def run_health_check(self) -> dict:
        """Run comprehensive health check"""
        print(f"🔍 Running SEO health check for {self.base_url}")
        
        health_check = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'sitemap': self.check_sitemap(),
            'seo_pages': self.check_seo_pages(),
            'api_endpoints': self.check_api_endpoints()
        }
        
        # Calculate health score
        total_checks = 0
        passed_checks = 0
        
        # Sitemap check
        total_checks += 1
        if health_check['sitemap']['accessible']:
            passed_checks += 1
        
        # SEO pages check
        for page, result in health_check['seo_pages'].items():
            total_checks += 1
            if result['accessible']:
                passed_checks += 1
        
        # API endpoints check
        for endpoint, result in health_check['api_endpoints'].items():
            total_checks += 1
            if result['accessible']:
                passed_checks += 1
        
        health_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        health_check['health_score'] = round(health_score, 1)
        health_check['total_checks'] = total_checks
        health_check['passed_checks'] = passed_checks
        
        return health_check
    
    def generate_report(self, health_check: dict) -> str:
        """Generate health check report"""
        report = f"""
# TenderPulse SEO Health Check Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🏥 Overall Health Score: {health_check['health_score']}%
**Passed:** {health_check['passed_checks']}/{health_check['total_checks']} checks

## 🗺️ Sitemap Status
- **Status:** {'✅ ACCESSIBLE' if health_check['sitemap']['accessible'] else '❌ NOT ACCESSIBLE'}
- **URL Count:** {health_check['sitemap'].get('url_count', 'Unknown')}
- **Response Time:** {health_check['sitemap']['response_time']}s
"""
        
        if not health_check['sitemap']['accessible']:
            report += f"- **Error:** {health_check['sitemap'].get('error', 'Unknown error')}\n"
        
        report += "\n## 📄 SEO Pages Status\n"
        for page, result in health_check['seo_pages'].items():
            status_icon = "✅" if result['accessible'] else "❌"
            report += f"- {status_icon} {page} - HTTP {result['status_code']} ({result['response_time']}s)\n"
            if not result['accessible']:
                report += f"  - Error: {result.get('error', 'Unknown error')}\n"
        
        report += "\n## 🔌 API Endpoints Status\n"
        for endpoint, result in health_check['api_endpoints'].items():
            status_icon = "✅" if result['accessible'] else "❌"
            report += f"- {status_icon} {endpoint} - HTTP {result['status_code']} ({result['response_time']}s)\n"
            if not result['accessible']:
                report += f"  - Error: {result.get('error', 'Unknown error')}\n"
        
        # Recommendations
        report += "\n## 🎯 Recommendations\n"
        if health_check['health_score'] < 80:
            report += "- ⚠️ Health score is below 80% - investigate issues\n"
        
        if not health_check['sitemap']['accessible']:
            report += "- 🗺️ Fix sitemap issues - critical for SEO\n"
        
        failed_pages = [page for page, result in health_check['seo_pages'].items() if not result['accessible']]
        if failed_pages:
            report += f"- 📄 Fix {len(failed_pages)} inaccessible SEO pages\n"
        
        failed_apis = [endpoint for endpoint, result in health_check['api_endpoints'].items() if not result['accessible']]
        if failed_apis:
            report += f"- 🔌 Fix {len(failed_apis)} inaccessible API endpoints\n"
        
        if health_check['health_score'] >= 90:
            report += "- 🎉 Excellent health score! Consider scaling content\n"
        elif health_check['health_score'] >= 70:
            report += "- 👍 Good health score! Minor optimizations needed\n"
        else:
            report += "- 🚨 Poor health score! Immediate action required\n"
        
        return report
    
    def save_results(self, health_check: dict):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"seo_health_check_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(health_check, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Health check saved to {filename}")
        return filename

def main():
    """Main function"""
    checker = SimpleSEOChecker()
    
    # Run health check
    health_check = checker.run_health_check()
    
    # Generate report
    report = checker.generate_report(health_check)
    print(report)
    
    # Save results
    checker.save_results(health_check)
    
    # Save report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f"seo_health_report_{timestamp}.md"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Report saved to {report_filename}")
    
    # Next steps
    print("\n🚀 Next Steps:")
    print("1. Follow the instructions in google_search_console_setup.md")
    print("2. Fix any issues identified in this report")
    print("3. Wait for deployments to complete")
    print("4. Re-run this check in a few hours")
    print("5. Set up Google Search Console once everything is working")

if __name__ == "__main__":
    main()
