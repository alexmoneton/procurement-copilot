#!/usr/bin/env python3
"""
TenderPulse SEO Monitoring Dashboard
Automated SEO performance tracking and optimization
"""

import asyncio
import aiohttp
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from dataclasses import dataclass
import time

@dataclass
class SEOStats:
    """SEO performance statistics"""
    url: str
    title: str
    status_code: int
    response_time: float
    page_size: int
    has_meta_description: bool
    has_structured_data: bool
    internal_links: int
    external_links: int
    images_with_alt: int
    total_images: int
    h1_count: int
    h2_count: int
    word_count: int
    last_checked: datetime

class SEOMonitor:
    """SEO monitoring and optimization system"""
    
    def __init__(self, base_url: str = "https://tenderpulse.eu"):
        self.base_url = base_url
        self.session = None
        self.results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_page_seo(self, url: str) -> SEOStats:
        """Check SEO metrics for a single page"""
        start_time = time.time()
        
        try:
            async with self.session.get(url, timeout=30) as response:
                content = await response.text()
                response_time = time.time() - start_time
                
                # Basic metrics
                page_size = len(content.encode('utf-8'))
                status_code = response.status
                
                # Parse HTML for SEO elements
                has_meta_description = 'name="description"' in content
                has_structured_data = 'application/ld+json' in content
                
                # Count elements
                internal_links = content.count(f'href="{self.base_url}')
                external_links = content.count('href="http') - internal_links
                images_with_alt = content.count('alt="')
                total_images = content.count('<img')
                h1_count = content.count('<h1')
                h2_count = content.count('<h2')
                
                # Estimate word count (rough)
                word_count = len(content.split())
                
                # Extract title
                title_start = content.find('<title>')
                title_end = content.find('</title>')
                title = content[title_start+7:title_end] if title_start != -1 and title_end != -1 else "No title"
                
                return SEOStats(
                    url=url,
                    title=title,
                    status_code=status_code,
                    response_time=response_time,
                    page_size=page_size,
                    has_meta_description=has_meta_description,
                    has_structured_data=has_structured_data,
                    internal_links=internal_links,
                    external_links=external_links,
                    images_with_alt=images_with_alt,
                    total_images=total_images,
                    h1_count=h1_count,
                    h2_count=h2_count,
                    word_count=word_count,
                    last_checked=datetime.now()
                )
                
        except Exception as e:
            print(f"Error checking {url}: {e}")
            return SEOStats(
                url=url,
                title="Error",
                status_code=0,
                response_time=0,
                page_size=0,
                has_meta_description=False,
                has_structured_data=False,
                internal_links=0,
                external_links=0,
                images_with_alt=0,
                total_images=0,
                h1_count=0,
                h2_count=0,
                word_count=0,
                last_checked=datetime.now()
            )
    
    async def get_sitemap_urls(self) -> List[str]:
        """Get all URLs from sitemap"""
        urls = []
        
        # Static pages
        static_pages = [
            "/",
            "/pricing",
            "/app",
            "/terms",
            "/privacy"
        ]
        
        # SEO pages (countries)
        countries = ['es', 'gb', 'de', 'fr', 'it', 'nl', 'be', 'at', 'dk', 'se', 'fi', 'no']
        for country in countries:
            urls.append(f"/seo/countries/{country}")
        
        # SEO pages (CPV codes)
        cpv_codes = ['72000000', '79400000', '45000000', '48000000', '71000000', '73000000']
        for cpv in cpv_codes:
            urls.append(f"/seo/cpv-codes/{cpv}")
        
        # SEO pages (value ranges)
        value_ranges = ['small', 'medium', 'large', 'enterprise']
        for range_type in value_ranges:
            urls.append(f"/seo/value-ranges/{range_type}")
        
        # Tender combination pages (sample)
        combinations = [
            ("de", "information-technology", "2024", "500k-2m"),
            ("fr", "construction", "2024", "2m-10m"),
            ("es", "consulting", "2024", "100k-500k"),
            ("nl", "medical-equipment", "2024", "100k-500k"),
            ("gb", "transportation", "2024", "2m-10m")
        ]
        
        for country, category, year, budget in combinations:
            urls.append(f"/seo/tenders/{country}/{category}/{year}/{budget}")
        
        return [f"{self.base_url}{url}" for url in urls]
    
    async def run_seo_audit(self) -> List[SEOStats]:
        """Run comprehensive SEO audit"""
        print("🔍 Starting SEO audit...")
        
        urls = await self.get_sitemap_urls()
        print(f"📊 Checking {len(urls)} pages...")
        
        # Check pages in batches
        batch_size = 10
        results = []
        
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i+batch_size]
            print(f"⏳ Processing batch {i//batch_size + 1}/{(len(urls)-1)//batch_size + 1}")
            
            tasks = [self.check_page_seo(url) for url in batch]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        self.results = results
        return results
    
    def generate_report(self) -> str:
        """Generate SEO audit report"""
        if not self.results:
            return "No results to report"
        
        total_pages = len(self.results)
        successful_pages = len([r for r in self.results if r.status_code == 200])
        failed_pages = total_pages - successful_pages
        
        avg_response_time = sum(r.response_time for r in self.results) / total_pages
        avg_page_size = sum(r.page_size for r in self.results) / total_pages
        
        pages_with_meta = len([r for r in self.results if r.has_meta_description])
        pages_with_structured_data = len([r for r in self.results if r.has_structured_data])
        
        # Issues
        issues = []
        for result in self.results:
            if result.status_code != 200:
                issues.append(f"❌ {result.url} - HTTP {result.status_code}")
            if not result.has_meta_description:
                issues.append(f"⚠️ {result.url} - Missing meta description")
            if not result.has_structured_data:
                issues.append(f"⚠️ {result.url} - Missing structured data")
            if result.h1_count == 0:
                issues.append(f"⚠️ {result.url} - Missing H1 tag")
            if result.h1_count > 1:
                issues.append(f"⚠️ {result.url} - Multiple H1 tags ({result.h1_count})")
            if result.response_time > 3.0:
                issues.append(f"🐌 {result.url} - Slow loading ({result.response_time:.2f}s)")
            if result.page_size > 1000000:  # 1MB
                issues.append(f"📦 {result.url} - Large page size ({result.page_size/1024:.0f}KB)")
        
        report = f"""
# TenderPulse SEO Audit Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Summary
- **Total Pages Checked:** {total_pages}
- **Successful Pages:** {successful_pages} ({successful_pages/total_pages*100:.1f}%)
- **Failed Pages:** {failed_pages} ({failed_pages/total_pages*100:.1f}%)
- **Average Response Time:** {avg_response_time:.2f}s
- **Average Page Size:** {avg_page_size/1024:.0f}KB

## 🎯 SEO Metrics
- **Pages with Meta Descriptions:** {pages_with_meta}/{total_pages} ({pages_with_meta/total_pages*100:.1f}%)
- **Pages with Structured Data:** {pages_with_structured_data}/{total_pages} ({pages_with_structured_data/total_pages*100:.1f}%)

## 🚨 Issues Found ({len(issues)})
"""
        
        for issue in issues[:20]:  # Show first 20 issues
            report += f"{issue}\n"
        
        if len(issues) > 20:
            report += f"... and {len(issues) - 20} more issues\n"
        
        # Top performing pages
        successful_results = [r for r in self.results if r.status_code == 200]
        if successful_results:
            fastest_pages = sorted(successful_results, key=lambda x: x.response_time)[:5]
            report += "\n## 🚀 Fastest Pages\n"
            for page in fastest_pages:
                report += f"- {page.url} ({page.response_time:.2f}s)\n"
        
        return report
    
    def save_to_csv(self, filename: str = "seo_audit_results.csv"):
        """Save results to CSV file"""
        if not self.results:
            print("No results to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'url', 'title', 'status_code', 'response_time', 'page_size',
                'has_meta_description', 'has_structured_data', 'internal_links',
                'external_links', 'images_with_alt', 'total_images', 'h1_count',
                'h2_count', 'word_count', 'last_checked'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                writer.writerow({
                    'url': result.url,
                    'title': result.title,
                    'status_code': result.status_code,
                    'response_time': result.response_time,
                    'page_size': result.page_size,
                    'has_meta_description': result.has_meta_description,
                    'has_structured_data': result.has_structured_data,
                    'internal_links': result.internal_links,
                    'external_links': result.external_links,
                    'images_with_alt': result.images_with_alt,
                    'total_images': result.total_images,
                    'h1_count': result.h1_count,
                    'h2_count': result.h2_count,
                    'word_count': result.word_count,
                    'last_checked': result.last_checked.isoformat()
                })
        
        print(f"📁 Results saved to {filename}")

async def main():
    """Main function to run SEO audit"""
    async with SEOMonitor() as monitor:
        # Run SEO audit
        results = await monitor.run_seo_audit()
        
        # Generate report
        report = monitor.generate_report()
        print(report)
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"seo_audit_report_{timestamp}.md"
        csv_filename = f"seo_audit_results_{timestamp}.csv"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        monitor.save_to_csv(csv_filename)
        
        print(f"\n📄 Report saved to {report_filename}")
        print(f"📊 Data saved to {csv_filename}")

if __name__ == "__main__":
    asyncio.run(main())
