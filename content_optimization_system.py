#!/usr/bin/env python3
"""
TenderPulse Content Optimization System
Automated content analysis and optimization recommendations
"""

import asyncio
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

@dataclass
class ContentAnalysis:
    """Content analysis results"""
    url: str
    title: str
    word_count: int
    readability_score: float
    keyword_density: Dict[str, float]
    heading_structure: Dict[str, int]
    internal_links: int
    external_links: int
    images: int
    recommendations: List[str]

class ContentOptimizer:
    """Content optimization and analysis system"""
    
    def __init__(self, base_url: str = "https://tenderpulse.eu"):
        self.base_url = base_url
        self.session = None
        
        # Target keywords for EU procurement
        self.target_keywords = [
            "government tenders",
            "public procurement",
            "EU tenders",
            "government contracts",
            "public sector opportunities",
            "procurement opportunities",
            "tender opportunities",
            "government bidding",
            "public contracts",
            "EU procurement"
        ]
        
        # Country-specific keywords
        self.country_keywords = {
            'germany': ['german tenders', 'deutschland ausschreibungen', 'bundesregierung'],
            'france': ['appels d\'offres', 'marchés publics', 'gouvernement français'],
            'spain': ['licitaciones', 'contratos públicos', 'gobierno español'],
            'italy': ['gare pubbliche', 'appalti', 'governo italiano'],
            'netherlands': ['aanbestedingen', 'overheidsopdrachten', 'nederlandse overheid'],
            'united kingdom': ['uk tenders', 'government contracts', 'public sector'],
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def calculate_readability(self, text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        sentences = len(re.findall(r'[.!?]+', text))
        words = len(text.split())
        syllables = sum(self.count_syllables(word) for word in text.split())
        
        if sentences == 0 or words == 0:
            return 0
        
        score = 206.835 - (1.015 * (words / sentences)) - (84.6 * (syllables / words))
        return max(0, min(100, score))
    
    def count_syllables(self, word: str) -> int:
        """Count syllables in a word"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel
        
        if word.endswith('e'):
            syllable_count -= 1
        
        return max(1, syllable_count)
    
    def analyze_keyword_density(self, text: str) -> Dict[str, float]:
        """Analyze keyword density in text"""
        text_lower = text.lower()
        word_count = len(text.split())
        keyword_density = {}
        
        for keyword in self.target_keywords:
            count = text_lower.count(keyword.lower())
            density = (count / word_count) * 100 if word_count > 0 else 0
            keyword_density[keyword] = round(density, 2)
        
        return keyword_density
    
    def analyze_heading_structure(self, html: str) -> Dict[str, int]:
        """Analyze heading structure"""
        headings = {
            'h1': len(re.findall(r'<h1[^>]*>', html, re.IGNORECASE)),
            'h2': len(re.findall(r'<h2[^>]*>', html, re.IGNORECASE)),
            'h3': len(re.findall(r'<h3[^>]*>', html, re.IGNORECASE)),
            'h4': len(re.findall(r'<h4[^>]*>', html, re.IGNORECASE)),
            'h5': len(re.findall(r'<h5[^>]*>', html, re.IGNORECASE)),
            'h6': len(re.findall(r'<h6[^>]*>', html, re.IGNORECASE))
        }
        return headings
    
    def generate_recommendations(self, analysis: ContentAnalysis) -> List[str]:
        """Generate content optimization recommendations"""
        recommendations = []
        
        # Word count recommendations
        if analysis.word_count < 300:
            recommendations.append("📝 Add more content - aim for at least 300 words")
        elif analysis.word_count > 2000:
            recommendations.append("✂️ Consider breaking long content into multiple pages")
        
        # Readability recommendations
        if analysis.readability_score < 30:
            recommendations.append("📖 Improve readability - use shorter sentences and simpler words")
        elif analysis.readability_score > 80:
            recommendations.append("🎯 Content might be too simple - add more technical details")
        
        # Keyword density recommendations
        low_density_keywords = [k for k, v in analysis.keyword_density.items() if v < 0.5]
        if low_density_keywords:
            recommendations.append(f"🔍 Increase keyword density for: {', '.join(low_density_keywords[:3])}")
        
        high_density_keywords = [k for k, v in analysis.keyword_density.items() if v > 3]
        if high_density_keywords:
            recommendations.append(f"⚠️ Reduce keyword density for: {', '.join(high_density_keywords[:3])}")
        
        # Heading structure recommendations
        if analysis.heading_structure['h1'] == 0:
            recommendations.append("🏷️ Add an H1 tag to improve SEO structure")
        elif analysis.heading_structure['h1'] > 1:
            recommendations.append("🏷️ Use only one H1 tag per page")
        
        if analysis.heading_structure['h2'] == 0:
            recommendations.append("📋 Add H2 tags to organize content sections")
        
        # Link recommendations
        if analysis.internal_links < 3:
            recommendations.append("🔗 Add more internal links to related pages")
        
        if analysis.external_links == 0:
            recommendations.append("🌐 Add relevant external links for authority")
        
        # Image recommendations
        if analysis.images == 0:
            recommendations.append("🖼️ Add relevant images to improve engagement")
        elif analysis.images > 10:
            recommendations.append("🖼️ Consider reducing number of images for faster loading")
        
        return recommendations
    
    async def analyze_page_content(self, url: str) -> ContentAnalysis:
        """Analyze content of a single page"""
        try:
            async with self.session.get(url, timeout=30) as response:
                html = await response.text()
                
                # Extract text content (basic implementation)
                text = re.sub(r'<[^>]+>', ' ', html)
                text = re.sub(r'\s+', ' ', text).strip()
                
                # Extract title
                title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
                title = title_match.group(1).strip() if title_match else "No title"
                
                # Analyze content
                word_count = len(text.split())
                readability_score = self.calculate_readability(text)
                keyword_density = self.analyze_keyword_density(text)
                heading_structure = self.analyze_heading_structure(html)
                
                # Count links and images
                internal_links = len(re.findall(rf'href="{re.escape(self.base_url)}', html))
                external_links = len(re.findall(r'href="https?://(?!' + re.escape(self.base_url.replace('https://', '')) + ')', html))
                images = len(re.findall(r'<img[^>]*>', html, re.IGNORECASE))
                
                analysis = ContentAnalysis(
                    url=url,
                    title=title,
                    word_count=word_count,
                    readability_score=readability_score,
                    keyword_density=keyword_density,
                    heading_structure=heading_structure,
                    internal_links=internal_links,
                    external_links=external_links,
                    images=images,
                    recommendations=[]
                )
                
                analysis.recommendations = self.generate_recommendations(analysis)
                return analysis
                
        except Exception as e:
            print(f"Error analyzing {url}: {e}")
            return ContentAnalysis(
                url=url,
                title="Error",
                word_count=0,
                readability_score=0,
                keyword_density={},
                heading_structure={},
                internal_links=0,
                external_links=0,
                images=0,
                recommendations=["❌ Failed to analyze page"]
            )
    
    async def analyze_seo_pages(self) -> List[ContentAnalysis]:
        """Analyze all SEO pages"""
        print("🔍 Analyzing SEO pages content...")
        
        # Sample SEO pages to analyze
        pages_to_analyze = [
            f"{self.base_url}/seo/countries/de",
            f"{self.base_url}/seo/countries/fr",
            f"{self.base_url}/seo/countries/es",
            f"{self.base_url}/seo/cpv-codes/72000000",
            f"{self.base_url}/seo/cpv-codes/45000000",
            f"{self.base_url}/seo/value-ranges/medium",
            f"{self.base_url}/seo/value-ranges/large",
        ]
        
        results = []
        for url in pages_to_analyze:
            print(f"⏳ Analyzing {url}")
            analysis = await self.analyze_page_content(url)
            results.append(analysis)
            await asyncio.sleep(1)  # Be respectful to the server
        
        return results
    
    def generate_optimization_report(self, analyses: List[ContentAnalysis]) -> str:
        """Generate content optimization report"""
        if not analyses:
            return "No analyses to report"
        
        total_pages = len(analyses)
        avg_word_count = sum(a.word_count for a in analyses) / total_pages
        avg_readability = sum(a.readability_score for a in analyses) / total_pages
        
        # Collect all recommendations
        all_recommendations = []
        for analysis in analyses:
            all_recommendations.extend(analysis.recommendations)
        
        # Count recommendation frequency
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        # Sort by frequency
        sorted_recommendations = sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)
        
        report = f"""
# TenderPulse Content Optimization Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Content Analysis Summary
- **Total Pages Analyzed:** {total_pages}
- **Average Word Count:** {avg_word_count:.0f} words
- **Average Readability Score:** {avg_readability:.1f}/100

## 🎯 Top Optimization Recommendations
"""
        
        for rec, count in sorted_recommendations[:10]:
            percentage = (count / total_pages) * 100
            report += f"- {rec} ({count}/{total_pages} pages - {percentage:.0f}%)\n"
        
        report += "\n## 📄 Page-by-Page Analysis\n"
        
        for analysis in analyses:
            report += f"""
### {analysis.title}
**URL:** {analysis.url}
**Word Count:** {analysis.word_count}
**Readability:** {analysis.readability_score:.1f}/100
**Internal Links:** {analysis.internal_links}
**External Links:** {analysis.external_links}
**Images:** {analysis.images}

**Recommendations:**
"""
            for rec in analysis.recommendations:
                report += f"- {rec}\n"
        
        return report
    
    def generate_content_ideas(self) -> str:
        """Generate content ideas for SEO pages"""
        return """
# Content Ideas for TenderPulse SEO Pages

## 🎯 High-Value Content Topics

### 1. Country-Specific Content
- "Complete Guide to [Country] Government Tenders"
- "[Country] Public Procurement Laws and Regulations"
- "How to Win [Country] Government Contracts"
- "[Country] Tender Deadlines and Submission Process"

### 2. Industry-Specific Content
- "IT Services Tenders: What Buyers Look For"
- "Construction Tenders: Compliance Requirements"
- "Healthcare Equipment Procurement Process"
- "Environmental Services Tender Opportunities"

### 3. Value-Based Content
- "Small Business Government Contracting Guide"
- "Enterprise-Level Procurement Strategies"
- "Medium-Size Company Tender Success Tips"

### 4. Educational Content
- "Understanding CPV Codes for EU Tenders"
- "EU Procurement Directives Explained"
- "Tender Evaluation Criteria Guide"
- "Bidding Strategy for Public Contracts"

## 📝 Content Optimization Tips

### For Country Pages:
1. **Add Local Context**: Include country-specific procurement laws
2. **Local Keywords**: Use local language terms where relevant
3. **Success Stories**: Add case studies from that country
4. **Local Resources**: Link to local procurement portals

### For CPV Code Pages:
1. **Technical Details**: Explain what the CPV code covers
2. **Industry Examples**: Show real tender examples
3. **Requirements**: List typical requirements for this category
4. **Tips**: Provide bidding tips specific to this category

### For Value Range Pages:
1. **Company Size Guidance**: Help companies understand if they fit
2. **Competition Analysis**: Explain typical competition levels
3. **Resource Requirements**: Detail what's needed to compete
4. **Success Metrics**: Show typical success rates

## 🔗 Internal Linking Strategy

### Hub Pages:
- Create category hub pages (e.g., "/it-tenders", "/construction-tenders")
- Link from hub pages to specific country/CPV combinations
- Use breadcrumb navigation

### Cross-Linking:
- Link between related countries (e.g., Germany ↔ Austria)
- Link between related CPV codes
- Link between different value ranges for the same category

### Content Clusters:
- Group related content together
- Create topic clusters around major themes
- Use consistent internal linking patterns

## 📊 Content Performance Tracking

### Key Metrics:
- **Page Views**: Track which content gets most traffic
- **Time on Page**: Measure engagement
- **Bounce Rate**: Identify content that doesn't engage
- **Conversion Rate**: Track which content converts to signups

### A/B Testing Ideas:
- Test different title formats
- Test different content lengths
- Test different call-to-action placements
- Test different internal linking strategies
"""

async def main():
    """Main function to run content optimization analysis"""
    async with ContentOptimizer() as optimizer:
        # Analyze SEO pages
        analyses = await optimizer.analyze_seo_pages()
        
        # Generate optimization report
        report = optimizer.generate_optimization_report(analyses)
        print(report)
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"content_optimization_report_{timestamp}.md"
        
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Generate content ideas
        content_ideas = optimizer.generate_content_ideas()
        ideas_filename = f"content_ideas_{timestamp}.md"
        
        with open(ideas_filename, 'w', encoding='utf-8') as f:
            f.write(content_ideas)
        
        print(f"\n📄 Optimization report saved to {report_filename}")
        print(f"💡 Content ideas saved to {ideas_filename}")

if __name__ == "__main__":
    asyncio.run(main())
