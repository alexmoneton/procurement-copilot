import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    // Fetch sitemap data from backend
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.tenderpulse.eu'
    const response = await fetch(`${apiUrl}/api/v1/seo/sitemap-data`, {
      headers: {
        'Accept': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`API responded with status: ${response.status}`)
    }

    const combinations = await response.json()
    
    const sitemap = generateSitemapXML(combinations)
    
    return new NextResponse(sitemap, {
      status: 200,
      headers: {
        'Content-Type': 'text/xml',
        'Cache-Control': 'public, max-age=86400, stale-while-revalidate=604800',
      },
    })
  } catch (error) {
    console.error('Sitemap generation error:', error)
    
    // Return a basic sitemap if API fails
    const fallbackSitemap = generateFallbackSitemap()
    
    return new NextResponse(fallbackSitemap, {
      status: 200,
      headers: {
        'Content-Type': 'text/xml',
        'Cache-Control': 'public, max-age=3600', // Shorter cache for fallback
      },
    })
  }
}

function generateSitemapXML(combinations: any[]): string {
  const baseUrl = 'https://tenderpulse.eu'
  const now = new Date().toISOString().split('T')[0]
  
  const staticPages = [
    { path: '/', priority: '1.0', changefreq: 'daily' },
    { path: '/pricing', priority: '0.9', changefreq: 'weekly' },
    { path: '/app', priority: '0.8', changefreq: 'daily' },
    { path: '/terms', priority: '0.3', changefreq: 'monthly' },
    { path: '/privacy', priority: '0.3', changefreq: 'monthly' },
  ]
  
  // Add existing SEO pages
  const seoPages = [
    // Countries
    { path: '/seo/countries/es', priority: '0.7', changefreq: 'daily' },
    { path: '/seo/countries/gb', priority: '0.7', changefreq: 'daily' },
    { path: '/seo/countries/de', priority: '0.7', changefreq: 'daily' },
    { path: '/seo/countries/fr', priority: '0.7', changefreq: 'daily' },
    { path: '/seo/countries/it', priority: '0.7', changefreq: 'daily' },
    { path: '/seo/countries/nl', priority: '0.7', changefreq: 'daily' },
    
    // CPV Codes
    { path: '/seo/cpv-codes/72000000', priority: '0.6', changefreq: 'daily' },
    { path: '/seo/cpv-codes/79400000', priority: '0.6', changefreq: 'daily' },
    { path: '/seo/cpv-codes/45000000', priority: '0.6', changefreq: 'daily' },
    { path: '/seo/cpv-codes/48000000', priority: '0.6', changefreq: 'daily' },
    
    // Value Ranges
    { path: '/seo/value-ranges/small', priority: '0.6', changefreq: 'daily' },
    { path: '/seo/value-ranges/medium', priority: '0.6', changefreq: 'daily' },
    { path: '/seo/value-ranges/large', priority: '0.6', changefreq: 'daily' },
    { path: '/seo/value-ranges/enterprise', priority: '0.6', changefreq: 'daily' },
  ]
  
  const urls = [
    ...staticPages.map(page => 
      `<url>
         <loc>${baseUrl}${page.path}</loc>
         <lastmod>${now}</lastmod>
         <changefreq>${page.changefreq}</changefreq>
         <priority>${page.priority}</priority>
       </url>`
    ),
    ...seoPages.map(page => 
      `<url>
         <loc>${baseUrl}${page.path}</loc>
         <lastmod>${now}</lastmod>
         <changefreq>${page.changefreq}</changefreq>
         <priority>${page.priority}</priority>
       </url>`
    ),
    ...combinations.map(combo => {
      const country = combo.country.toLowerCase()
      const category = combo.category.toLowerCase().replace(/\s+/g, '-')
      const year = combo.year.toString()
      const budget = combo.budget.toLowerCase().replace(/\s+/g, '-')
      
      return `<url>
                <loc>${baseUrl}/seo/tenders/${country}/${category}/${year}/${budget}</loc>
                <lastmod>${now}</lastmod>
                <changefreq>daily</changefreq>
                <priority>0.8</priority>
              </url>`
    })
  ]
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${urls.join('\n  ')}
</urlset>`
}

function generateFallbackSitemap(): string {
  const baseUrl = 'https://tenderpulse.eu'
  const now = new Date().toISOString().split('T')[0]
  
  const staticPages = [
    { path: '/', priority: '1.0', changefreq: 'daily' },
    { path: '/pricing', priority: '0.9', changefreq: 'weekly' },
    { path: '/app', priority: '0.8', changefreq: 'daily' },
    { path: '/terms', priority: '0.3', changefreq: 'monthly' },
    { path: '/privacy', priority: '0.3', changefreq: 'monthly' },
  ]
  
  const urls = staticPages.map(page => 
    `<url>
       <loc>${baseUrl}${page.path}</loc>
       <lastmod>${now}</lastmod>
       <changefreq>${page.changefreq}</changefreq>
       <priority>${page.priority}</priority>
     </url>`
  )
  
  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  ${urls.join('\n  ')}
</urlset>`
}
