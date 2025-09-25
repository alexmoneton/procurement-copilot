#!/usr/bin/env python3
"""
TenderPulse Automated SEO Workflow
Complete SEO automation system for monitoring, optimization, and scaling
"""

import asyncio
import aiohttp
import json
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class AutomatedSEOWorkflow:
    """Automated SEO workflow management system"""
    
    def __init__(self, base_url: str = "https://tenderpulse.eu"):
        self.base_url = base_url
        self.session = None
        self.results_history = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_sitemap_status(self) -> Dict:
        """Check if sitemap is accessible and valid"""
        try:
            sitemap_url = f"{self.base_url}/sitemap.xml"
            async with self.session.get(sitemap_url, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    url_count = content.count('<url>')
                    return {
                        'status': 'success',
                        'url_count': url_count,
                        'last_modified': response.headers.get('last-modified', 'Unknown'),
                        'content_length': len(content)
                    }
                else:
                    return {
                        'status': 'error',
                        'error': f'HTTP {response.status}',
                        'url_count': 0
                    }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'url_count': 0
            }
    
    async def check_seo_pages_status(self) -> Dict:
        """Check status of key SEO pages"""
        key_pages = [
            "/seo/countries/de",
            "/seo/countries/fr", 
            "/seo/countries/es",
            "/seo/cpv-codes/72000000",
            "/seo/cpv-codes/45000000",
            "/seo/value-ranges/medium"
        ]
        
        results = {}
        for page in key_pages:
            try:
                url = f"{self.base_url}{page}"
                async with self.session.get(url, timeout=30) as response:
                    results[page] = {
                        'status_code': response.status,
                        'response_time': response.headers.get('x-response-time', 'Unknown'),
                        'accessible': response.status == 200
                    }
            except Exception as e:
                results[page] = {
                    'status_code': 0,
                    'error': str(e),
                    'accessible': False
                }
        
        return results
    
    async def check_backend_api_status(self) -> Dict:
        """Check if backend API endpoints are working"""
        api_endpoints = [
            "/api/v1/seo/tenders",
            "/api/v1/seo/sitemap-data",
            "/api/v1/seo/page-intro"
        ]
        
        results = {}
        for endpoint in api_endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                async with self.session.get(url, timeout=30) as response:
                    results[endpoint] = {
                        'status_code': response.status,
                        'accessible': response.status == 200
                    }
            except Exception as e:
                results[endpoint] = {
                    'status_code': 0,
                    'error': str(e),
                    'accessible': False
                }
        
        return results
    
    async def run_health_check(self) -> Dict:
        """Run comprehensive health check"""
        print(f"🔍 Running SEO health check for {self.base_url}")
        
        health_check = {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'sitemap': await self.check_sitemap_status(),
            'seo_pages': await self.check_seo_pages_status(),
            'api_endpoints': await self.check_backend_api_status()
        }
        
        # Calculate overall health score
        total_checks = 0
        passed_checks = 0
        
        # Sitemap check
        total_checks += 1
        if health_check['sitemap']['status'] == 'success':
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
    
    def generate_health_report(self, health_check: Dict) -> str:
        """Generate health check report"""
        report = f"""
# TenderPulse SEO Health Check Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🏥 Overall Health Score: {health_check['health_score']}%
**Passed:** {health_check['passed_checks']}/{health_check['total_checks']} checks

## 🗺️ Sitemap Status
- **Status:** {health_check['sitemap']['status'].upper()}
- **URL Count:** {health_check['sitemap']['url_count']}
- **Last Modified:** {health_check['sitemap'].get('last_modified', 'Unknown')}
"""
        
        if health_check['sitemap']['status'] == 'error':
            report += f"- **Error:** {health_check['sitemap']['error']}\n"
        
        report += "\n## 📄 SEO Pages Status\n"
        for page, result in health_check['seo_pages'].items():
            status_icon = "✅" if result['accessible'] else "❌"
            report += f"- {status_icon} {page} - HTTP {result['status_code']}\n"
            if not result['accessible'] and 'error' in result:
                report += f"  - Error: {result['error']}\n"
        
        report += "\n## 🔌 API Endpoints Status\n"
        for endpoint, result in health_check['api_endpoints'].items():
            status_icon = "✅" if result['accessible'] else "❌"
            report += f"- {status_icon} {endpoint} - HTTP {result['status_code']}\n"
            if not result['accessible'] and 'error' in result:
                report += f"  - Error: {result['error']}\n"
        
        # Recommendations
        report += "\n## 🎯 Recommendations\n"
        if health_check['health_score'] < 80:
            report += "- ⚠️ Health score is below 80% - investigate issues\n"
        
        if health_check['sitemap']['status'] != 'success':
            report += "- 🗺️ Fix sitemap issues - critical for SEO\n"
        
        failed_pages = [page for page, result in health_check['seo_pages'].items() if not result['accessible']]
        if failed_pages:
            report += f"- 📄 Fix {len(failed_pages)} inaccessible SEO pages\n"
        
        failed_apis = [endpoint for endpoint, result in health_check['api_endpoints'].items() if not result['accessible']]
        if failed_apis:
            report += f"- 🔌 Fix {len(failed_apis)} inaccessible API endpoints\n"
        
        if health_check['health_score'] >= 90:
            report += "- 🎉 Excellent health score! Consider scaling content\n"
        
        return report
    
    def save_health_check(self, health_check: Dict):
        """Save health check results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"seo_health_check_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(health_check, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Health check saved to {filename}")
        return filename
    
    async def run_weekly_seo_audit(self):
        """Run weekly comprehensive SEO audit"""
        print("📊 Running weekly SEO audit...")
        
        # Import and run the SEO monitoring dashboard
        try:
            from seo_monitoring_dashboard import SEOMonitor
            
            async with SEOMonitor(self.base_url) as monitor:
                results = await monitor.run_seo_audit()
                report = monitor.generate_report()
                
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_filename = f"weekly_seo_audit_{timestamp}.md"
                
                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                print(f"📄 Weekly audit report saved to {report_filename}")
                return report
                
        except ImportError:
            print("❌ SEO monitoring dashboard not found")
            return "SEO monitoring dashboard not available"
    
    async def run_content_optimization(self):
        """Run content optimization analysis"""
        print("🔍 Running content optimization analysis...")
        
        try:
            from content_optimization_system import ContentOptimizer
            
            async with ContentOptimizer(self.base_url) as optimizer:
                analyses = await optimizer.analyze_seo_pages()
                report = optimizer.generate_optimization_report(analyses)
                
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                report_filename = f"content_optimization_{timestamp}.md"
                
                with open(report_filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                print(f"📄 Content optimization report saved to {report_filename}")
                return report
                
        except ImportError:
            print("❌ Content optimization system not found")
            return "Content optimization system not available"
    
    def generate_scaling_recommendations(self) -> str:
        """Generate recommendations for scaling content"""
        return """
# TenderPulse SEO Scaling Recommendations

## 🚀 Phase 1: Foundation (Weeks 1-4)
### Immediate Actions:
1. **Fix Critical Issues**
   - Ensure sitemap is accessible
   - Fix any 404 errors on SEO pages
   - Verify all API endpoints are working

2. **Google Search Console Setup**
   - Submit sitemap to Google Search Console
   - Verify domain ownership
   - Set up performance monitoring

3. **Content Quality**
   - Add meta descriptions to all pages
   - Implement structured data markup
   - Optimize page titles and headings

## 📈 Phase 2: Growth (Weeks 5-12)
### Content Expansion:
1. **Add More Countries**
   - Expand from 6 to 15+ EU countries
   - Add country-specific content and keywords
   - Include local procurement regulations

2. **Expand CPV Codes**
   - Add 20+ most common CPV codes
   - Create industry-specific landing pages
   - Add technical requirements for each category

3. **Value Range Granularity**
   - Add more specific value ranges
   - Create budget-specific guidance
   - Add company size recommendations

## 🎯 Phase 3: Optimization (Weeks 13-24)
### Advanced SEO:
1. **Content Clusters**
   - Create topic clusters around major themes
   - Implement comprehensive internal linking
   - Add related content suggestions

2. **User Experience**
   - Optimize page load speeds
   - Improve mobile responsiveness
   - Add interactive elements (filters, search)

3. **Conversion Optimization**
   - A/B test call-to-action buttons
   - Optimize signup flow from SEO pages
   - Add lead magnets (guides, templates)

## 🌍 Phase 4: Scale (Weeks 25+)
### Global Expansion:
1. **International Markets**
   - Add non-EU countries (UK, Switzerland, Norway)
   - Create region-specific content
   - Localize for different languages

2. **Advanced Features**
   - Add tender comparison tools
   - Implement advanced filtering
   - Create personalized recommendations

3. **Content Marketing**
   - Start a procurement blog
   - Create downloadable resources
   - Develop video content

## 📊 Success Metrics to Track:

### Technical SEO:
- **Pages Indexed**: Target 80%+ within 3 months
- **Page Load Speed**: < 3 seconds
- **Mobile Usability**: 100% mobile-friendly
- **Core Web Vitals**: All green

### Content Performance:
- **Organic Traffic**: 25%+ month-over-month growth
- **Keyword Rankings**: Top 10 for 50+ keywords
- **Click-Through Rate**: 2-5% from search results
- **Conversion Rate**: 2-5% visitors to signups

### Business Impact:
- **Lead Generation**: 100+ qualified leads/month
- **Customer Acquisition**: 20+ new customers/month
- **Revenue Growth**: 50%+ from organic traffic
- **Market Share**: Top 3 in EU procurement tools

## 🛠️ Tools and Resources:

### Monitoring Tools:
- Google Search Console (free)
- Google Analytics (free)
- Screaming Frog SEO Spider (paid)
- Ahrefs or SEMrush (paid)

### Content Tools:
- Grammarly (writing)
- Canva (visuals)
- Loom (video)
- Notion (content planning)

### Technical Tools:
- PageSpeed Insights (free)
- GTmetrix (free/paid)
- Mobile-Friendly Test (free)
- Rich Results Test (free)

## 📅 Weekly Schedule:

### Monday: Health Check
- Run automated health check
- Review Google Search Console
- Check for technical issues

### Wednesday: Content Review
- Analyze top-performing pages
- Identify content gaps
- Plan new content

### Friday: Performance Review
- Review traffic and rankings
- Analyze conversion metrics
- Plan optimizations

## 🎯 6-Month Goals:

1. **100+ Indexed Pages**: All SEO pages indexed
2. **10,000+ Monthly Visitors**: From organic search
3. **500+ Keywords Ranking**: In top 100 positions
4. **50+ New Customers**: From SEO traffic
5. **€50,000+ Revenue**: From organic leads

## 🚨 Red Flags to Watch:

- **Health Score < 80%**: Investigate immediately
- **Traffic Drop > 20%**: Check for penalties
- **Indexing Rate < 50%**: Fix technical issues
- **Conversion Rate < 1%**: Optimize user experience
- **Page Speed > 5s**: Optimize performance
"""

async def main():
    """Main function to run automated SEO workflow"""
    async with AutomatedSEOWorkflow() as workflow:
        # Run health check
        health_check = await workflow.run_health_check()
        
        # Generate and save report
        report = workflow.generate_health_report(health_check)
        print(report)
        
        # Save health check data
        workflow.save_health_check(health_check)
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"seo_workflow_report_{timestamp}.md"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Generate scaling recommendations
        scaling_recommendations = workflow.generate_scaling_recommendations()
        scaling_filename = f"seo_scaling_recommendations_{timestamp}.md"
        
        with open(scaling_filename, 'w', encoding='utf-8') as f:
            f.write(scaling_recommendations)
        
        print(f"\n📄 Workflow report saved to {report_filename}")
        print(f"🚀 Scaling recommendations saved to {scaling_filename}")
        
        # Run additional audits if health score is good
        if health_check['health_score'] >= 70:
            print("\n🔄 Running additional audits...")
            await workflow.run_weekly_seo_audit()
            await workflow.run_content_optimization()
        else:
            print("\n⚠️ Health score is low - fix issues before running additional audits")

if __name__ == "__main__":
    asyncio.run(main())
