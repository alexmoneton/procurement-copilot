"""
Sitemap generation with proper chunking and crawl budget management
Implements Google's large-site crawl guidance
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
from fastapi import APIRouter, Query, Response
from fastapi.responses import PlainTextResponse

router = APIRouter()

# Load massive SEO dataset
_seo_tenders_cache = None

def load_massive_seo_data():
    """Load the massive SEO dataset."""
    global _seo_tenders_cache
    
    if _seo_tenders_cache is None:
        try:
            with open('massive_seo_tenders.json', 'r') as f:
                _seo_tenders_cache = json.load(f)
        except FileNotFoundError:
            _seo_tenders_cache = []
    
    return _seo_tenders_cache

def generate_sitemap_urls(urls: List[Dict[str, Any]], lastmod: str = None) -> str:
    """Generate XML sitemap from URL list."""
    if lastmod is None:
        lastmod = datetime.now().strftime('%Y-%m-%d')
    
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for url_data in urls:
        xml.append('  <url>')
        xml.append(f'    <loc>{url_data["loc"]}</loc>')
        xml.append(f'    <lastmod>{url_data.get("lastmod", lastmod)}</lastmod>')
        xml.append(f'    <changefreq>{url_data.get("changefreq", "weekly")}</changefreq>')
        xml.append(f'    <priority>{url_data.get("priority", "0.8")}</priority>')
        xml.append('  </url>')
    
    xml.append('</urlset>')
    return '\n'.join(xml)

def generate_sitemap_index(sitemaps: List[Dict[str, str]]) -> str:
    """Generate sitemap index XML."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    
    for sitemap in sitemaps:
        xml.append('  <sitemap>')
        xml.append(f'    <loc>{sitemap["loc"]}</loc>')
        xml.append(f'    <lastmod>{sitemap["lastmod"]}</lastmod>')
        xml.append('  </sitemap>')
    
    xml.append('</sitemapindex>')
    return '\n'.join(xml)

@router.get("/sitemap-index.xml", response_class=PlainTextResponse)
async def get_sitemap_index():
    """
    Generate sitemap index with all chunked sitemaps.
    Follows Google's guidance: ≤50k URLs per sitemap, ≤50MB each.
    """
    base_url = "https://tenderpulse.eu"
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    sitemaps = [
        {
            "loc": f"{base_url}/api/v1/sitemap/countries.xml",
            "lastmod": lastmod
        },
        {
            "loc": f"{base_url}/api/v1/sitemap/cpv-codes.xml", 
            "lastmod": lastmod
        },
        {
            "loc": f"{base_url}/api/v1/sitemap/value-ranges.xml",
            "lastmod": lastmod
        },
        {
            "loc": f"{base_url}/api/v1/sitemap/tenders.xml",
            "lastmod": lastmod
        }
    ]
    
    # Add country-specific sitemaps
    countries = ['es', 'de', 'fr', 'it', 'nl', 'gb', 'se', 'fi', 'dk', 'at', 'be', 'pl', 'cz', 'hu', 'ro', 'bg', 'hr', 'si', 'sk', 'lt', 'lv', 'ee', 'ie', 'pt', 'gr', 'cy', 'mt', 'lu']
    for country in countries:
        sitemaps.append({
            "loc": f"{base_url}/api/v1/sitemap/countries/{country}.xml",
            "lastmod": lastmod
        })
    
    xml_content = generate_sitemap_index(sitemaps)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/countries.xml", response_class=PlainTextResponse)
async def get_countries_sitemap():
    """Generate sitemap for country hub pages."""
    base_url = "https://tenderpulse.eu"
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    countries = ['es', 'de', 'fr', 'it', 'nl', 'gb', 'se', 'fi', 'dk', 'at', 'be', 'pl', 'cz', 'hu', 'ro', 'bg', 'hr', 'si', 'sk', 'lt', 'lv', 'ee', 'ie', 'pt', 'gr', 'cy', 'mt', 'lu']
    
    urls = []
    for country in countries:
        urls.append({
            "loc": f"{base_url}/seo/countries/{country}",
            "lastmod": lastmod,
            "changefreq": "daily",
            "priority": "0.9"
        })
    
    xml_content = generate_sitemap_urls(urls, lastmod)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/cpv-codes.xml", response_class=PlainTextResponse)
async def get_cpv_codes_sitemap():
    """Generate sitemap for CPV category pages."""
    base_url = "https://tenderpulse.eu"
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    # Major CPV codes
    cpv_codes = [
        '72000000-5', '79400000-8', '60100000-9', '34600000-0', '45000000-7',
        '48000000-8', '71000000-8', '73000000-2', '75000000-6', '80000000-4',
        '85000000-9', '90000000-7', '30000000-9', '31000000-6', '32000000-3',
        '33000000-0', '34000000-7', '35000000-2', '36000000-9', '37000000-1',
        '38000000-5', '39000000-2', '41000000-2', '42000000-6', '43000000-3',
        '44000000-0', '46000000-1', '47000000-3', '49000000-3', '50000000-5',
        '51000000-9', '52000000-9', '53000000-9', '54000000-7', '55000000-0',
        '56000000-2', '57000000-8', '58000000-8', '59000000-6', '60000000-8',
        '61000000-9', '62000000-8', '63000000-9', '64000000-6', '65000000-8',
        '66000000-6', '67000000-7', '68000000-8', '69000000-1', '70000000-1',
        '74000000-7', '76000000-5', '77000000-0', '78000000-7', '79000000-6',
        '80000000-4', '81000000-5', '82000000-1', '83000000-9', '84000000-5',
        '85000000-9', '86000000-7', '87000000-5', '88000000-9', '89000000-4',
        '90000000-7', '91000000-8', '92000000-1', '93000000-5', '94000000-2',
        '95000000-2', '96000000-1', '97000000-8', '98000000-5', '99000000-2'
    ]
    
    urls = []
    for cpv in cpv_codes:
        urls.append({
            "loc": f"{base_url}/seo/cpv-codes/{cpv}",
            "lastmod": lastmod,
            "changefreq": "weekly",
            "priority": "0.8"
        })
    
    xml_content = generate_sitemap_urls(urls, lastmod)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/value-ranges.xml", response_class=PlainTextResponse)
async def get_value_ranges_sitemap():
    """Generate sitemap for value range pages."""
    base_url = "https://tenderpulse.eu"
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    value_ranges = [
        "0-100000", "100000-500000", "500000-1000000", "1000000-2000000",
        "2000000-5000000", "5000000-10000000", "10000000-20000000",
        "20000000-50000000", "50000000-100000000", "100000000-500000000"
    ]
    
    urls = []
    for range_val in value_ranges:
        urls.append({
            "loc": f"{base_url}/seo/value-ranges/{range_val}",
            "lastmod": lastmod,
            "changefreq": "weekly",
            "priority": "0.7"
        })
    
    xml_content = generate_sitemap_urls(urls, lastmod)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/tenders.xml", response_class=PlainTextResponse)
async def get_tenders_sitemap():
    """Generate sitemap for individual tender pages (chunked)."""
    base_url = "https://tenderpulse.eu"
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    # Load tenders and chunk them
    tenders = load_massive_seo_data()
    
    # Limit to first 50k tenders to stay under Google's limit
    tenders = tenders[:50000]
    
    urls = []
    for tender in tenders:
        # Only include tenders that pass quality gates
        if passes_quality_gate(tender):
            urls.append({
                "loc": f"{base_url}/seo/tenders/{tender['id']}",
                "lastmod": lastmod,
                "changefreq": "monthly",
                "priority": "0.6"
            })
    
    xml_content = generate_sitemap_urls(urls, lastmod)
    return Response(content=xml_content, media_type="application/xml")

@router.get("/countries/{country}.xml", response_class=PlainTextResponse)
async def get_country_sitemap(country: str):
    """Generate sitemap for specific country's tender pages."""
    base_url = "https://tenderpulse.eu"
    lastmod = datetime.now().strftime('%Y-%m-%d')
    
    # Load tenders for this country
    tenders = load_massive_seo_data()
    country_tenders = [t for t in tenders if t.get('country', '').lower() == country.lower()]
    
    # Limit to 50k per sitemap
    country_tenders = country_tenders[:50000]
    
    urls = []
    for tender in country_tenders:
        if passes_quality_gate(tender):
            urls.append({
                "loc": f"{base_url}/seo/tenders/{tender['id']}",
                "lastmod": lastmod,
                "changefreq": "monthly",
                "priority": "0.6"
            })
    
    xml_content = generate_sitemap_urls(urls, lastmod)
    return Response(content=xml_content, media_type="application/xml")

def passes_quality_gate(tender: Dict[str, Any]) -> bool:
    """Simple quality gate - would be more sophisticated in production."""
    return (
        tender.get('title') and 
        tender.get('country') and 
        tender.get('value_amount', 0) > 0 and
        tender.get('buyer_name') and
        len(tender.get('title', '')) > 20
    )
