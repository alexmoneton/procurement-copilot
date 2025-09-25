import { MetadataRoute } from 'next'

// Country mapping
const COUNTRIES = [
  'ES', 'GB', 'DE', 'FR', 'IT', 'NL', 'BE', 'AT', 'DK', 'SE', 'FI', 'NO', 
  'CH', 'PL', 'CZ', 'HU', 'RO', 'BG', 'HR', 'SI', 'SK', 'LT', 'LV', 'EE', 
  'IE', 'PT', 'GR', 'CY', 'MT', 'LU'
]

// CPV codes
const CPV_CODES = [
  '72000000', '79400000', '60100000', '34600000', '45000000', '48000000',
  '71000000', '73000000', '75000000', '80000000', '85000000', '90000000'
]

// Value ranges
const VALUE_RANGES = ['small', 'medium', 'large', 'enterprise']

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://tenderpulse.eu'
  
  // Static pages
  const staticPages = [
    {
      url: baseUrl,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 1,
    },
    {
      url: `${baseUrl}/pricing`,
      lastModified: new Date(),
      changeFrequency: 'weekly' as const,
      priority: 0.8,
    },
    {
      url: `${baseUrl}/app`,
      lastModified: new Date(),
      changeFrequency: 'daily' as const,
      priority: 0.9,
    },
    {
      url: `${baseUrl}/terms`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.3,
    },
    {
      url: `${baseUrl}/privacy`,
      lastModified: new Date(),
      changeFrequency: 'monthly' as const,
      priority: 0.3,
    },
  ]

  // Country pages
  const countryPages = COUNTRIES.map((country) => ({
    url: `${baseUrl}/seo/countries/${country.toLowerCase()}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.7,
  }))

  // CPV code pages
  const cpvPages = CPV_CODES.map((cpv) => ({
    url: `${baseUrl}/seo/cpv-codes/${cpv}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.6,
  }))

  // Value range pages
  const valueRangePages = VALUE_RANGES.map((range) => ({
    url: `${baseUrl}/seo/value-ranges/${range}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.6,
  }))

  return [
    ...staticPages,
    ...countryPages,
    ...cpvPages,
    ...valueRangePages,
  ]
}
