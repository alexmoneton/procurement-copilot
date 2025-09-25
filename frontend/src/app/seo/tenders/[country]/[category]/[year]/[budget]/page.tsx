import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'

// Country mapping for better SEO
const COUNTRY_NAMES: Record<string, string> = {
  'es': 'Spain',
  'gb': 'United Kingdom', 
  'de': 'Germany',
  'fr': 'France',
  'it': 'Italy',
  'nl': 'Netherlands',
  'be': 'Belgium',
  'at': 'Austria',
  'dk': 'Denmark',
  'se': 'Sweden',
  'fi': 'Finland',
  'no': 'Norway',
  'ch': 'Switzerland',
  'pl': 'Poland',
  'cz': 'Czech Republic',
  'hu': 'Hungary',
  'ro': 'Romania',
  'bg': 'Bulgaria',
  'hr': 'Croatia',
  'si': 'Slovenia',
  'sk': 'Slovakia',
  'lt': 'Lithuania',
  'lv': 'Latvia',
  'ee': 'Estonia',
  'ie': 'Ireland',
  'pt': 'Portugal',
  'gr': 'Greece',
  'cy': 'Cyprus',
  'mt': 'Malta',
  'lu': 'Luxembourg'
}

const COUNTRY_FLAGS: Record<string, string> = {
  'es': '🇪🇸', 'gb': '🇬🇧', 'de': '🇩🇪', 'fr': '🇫🇷', 'it': '🇮🇹', 'nl': '🇳🇱',
  'be': '🇧🇪', 'at': '🇦🇹', 'dk': '🇩🇰', 'se': '🇸🇪', 'fi': '🇫🇮', 'no': '🇳🇴',
  'ch': '🇨🇭', 'pl': '🇵🇱', 'cz': '🇨🇿', 'hu': '🇭🇺', 'ro': '🇷🇴', 'bg': '🇧🇬',
  'hr': '🇭🇷', 'si': '🇸🇮', 'sk': '🇸🇰', 'lt': '🇱🇹', 'lv': '🇱🇻', 'ee': '🇪🇪',
  'ie': '🇮🇪', 'pt': '🇵🇹', 'gr': '🇬🇷', 'cy': '🇨🇾', 'mt': '🇲🇹', 'lu': '🇱🇺'
}

interface TenderCombinationPageProps {
  params: {
    country: string
    category: string
    year: string
    budget: string
  }
}

export async function generateMetadata({ params }: TenderCombinationPageProps): Promise<Metadata> {
  const countryCode = params.country.toLowerCase()
  const countryName = COUNTRY_NAMES[countryCode]
  const category = params.category.replace(/-/g, ' ')
  const year = params.year
  const budget = params.budget.replace(/-/g, ' ')
  
  if (!countryName) {
    return {
      title: 'Tender Combination Not Found - TenderPulse',
    }
  }

  const title = `${category} Tenders in ${countryName} ${year} | ${budget} Budget | TenderPulse`
  const description = `Find ${category} government tenders in ${countryName} for ${year} within the ${budget} budget range. Discover EU procurement opportunities with TenderPulse.`

  return {
    title,
    description,
    keywords: [
      `${category} tenders ${countryName}`,
      `${countryName} government contracts ${year}`,
      `${category} procurement ${countryName}`,
      `${budget} tenders ${countryName}`,
      `EU tenders ${countryName} ${year}`,
      `${category} opportunities ${countryName}`,
      `government bidding ${countryName}`,
      `public sector ${category} ${countryName}`
    ],
    openGraph: {
      title,
      description,
      type: 'website',
      locale: 'en_US',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
    },
    alternates: {
      canonical: `https://tenderpulse.eu/seo/tenders/${countryCode}/${params.category}/${year}/${params.budget}`,
    },
  }
}

export async function generateStaticParams() {
  // This would be populated from your API in production
  // For now, return some example combinations
  const combinations = [
    { country: 'de', category: 'information-technology', year: '2024', budget: '500k-2m' },
    { country: 'fr', category: 'construction', year: '2024', budget: '2m-10m' },
    { country: 'es', category: 'consulting', year: '2024', budget: '100k-500k' },
    { country: 'nl', category: 'medical-equipment', year: '2024', budget: '100k-500k' },
    { country: 'gb', category: 'transportation', year: '2024', budget: '2m-10m' },
  ]
  
  return combinations
}

async function getTendersForCombination(country: string, category: string, year: string, budget: string) {
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://api.tenderpulse.eu'
    const response = await fetch(`${apiUrl}/api/v1/seo/tenders?country=${country.toUpperCase()}&limit=20`, {
      headers: {
        'Accept': 'application/json',
      },
    })

    if (!response.ok) {
      return { tenders: [], total: 0, intro: '' }
    }

    const tenders = await response.json()
    
    // Get page intro
    const introResponse = await fetch(`${apiUrl}/api/v1/seo/page-intro?country=${country.toUpperCase()}&category=${category}&year=${parseInt(year)}&budget=${budget}`)
    const introData = introResponse.ok ? await introResponse.json() : { intro_text: '' }
    
    return {
      tenders: tenders || [],
      total: tenders?.length || 0,
      intro: introData.intro_text || ''
    }
  } catch (error) {
    console.error('Error fetching tenders:', error)
    return { tenders: [], total: 0, intro: '' }
  }
}

export default async function TenderCombinationPage({ params }: TenderCombinationPageProps) {
  const countryCode = params.country.toLowerCase()
  const countryName = COUNTRY_NAMES[countryCode]
  const category = params.category.replace(/-/g, ' ')
  const year = params.year
  const budget = params.budget.replace(/-/g, ' ')
  const flag = COUNTRY_FLAGS[countryCode]

  if (!countryName) {
    notFound()
  }

  const { tenders, total, intro } = await getTendersForCombination(
    countryCode, 
    params.category, 
    year, 
    params.budget
  )

  // Calculate total value
  const totalValue = tenders.reduce((sum: number, tender: any) => {
    return sum + (tender.value_amount || 0)
  }, 0)

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-EU', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center space-x-4 mb-6">
            <Link href="/" className="flex items-center space-x-2">
              <Image src="/logo.svg" alt="TenderPulse" width={32} height={32} className="h-8 w-8" />
              <span className="text-xl font-bold text-[#003399]" style={{fontFamily: 'Manrope, sans-serif'}}>
                TenderPulse
              </span>
            </Link>
          </div>
          
          <div className="text-center">
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 text-blue-800 text-sm font-medium mb-4">
              {flag} {countryName} • {category} • {year} • {budget}
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              {category} Tenders in {countryName} {year}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {intro || `Discover ${category} government tenders in ${countryName} for ${year} within the ${budget} budget range. Monitor ${countryName} public contracts and EU tenders in real-time.`}
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">{total}</div>
            <div className="text-gray-600">Active Tenders</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">
              {formatCurrency(totalValue)}
            </div>
            <div className="text-gray-600">Total Value</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">{year}</div>
            <div className="text-gray-600">Year</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">{budget}</div>
            <div className="text-gray-600">Budget Range</div>
          </div>
        </div>

        {/* Recent Tenders */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>
              {category} Tenders in {countryName} {year}
            </h2>
          </div>
          
          <div className="divide-y divide-gray-200">
            {tenders.map((tender: any) => (
              <div key={tender.id} className="p-6 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      <a 
                        href={tender.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="hover:text-[#003399] transition-colors"
                      >
                        {tender.title}
                      </a>
                    </h3>
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Buyer:</span> {tender.buyer_name || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Deadline:</span> {tender.deadline ? formatDate(tender.deadline) : 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Value:</span> {tender.value_amount ? formatCurrency(tender.value_amount) : 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Source:</span> {tender.source || 'N/A'}
                      </div>
                    </div>
                    
                    {tender.cpv_codes && tender.cpv_codes.length > 0 && (
                      <div className="mt-2">
                        <span className="font-medium text-sm text-gray-600">CPV Codes:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {tender.cpv_codes.slice(0, 3).map((code: string) => (
                            <span key={code} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                              {code}
                            </span>
                          ))}
                          {tender.cpv_codes.length > 3 && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-600">
                              +{tender.cpv_codes.length - 3} more
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          {tenders.length === 0 && (
            <div className="p-12 text-center text-gray-500">
              <p>No active tenders found for {category} in {countryName} {year} within the {budget} budget range.</p>
              <p className="mt-2">Check back soon for new opportunities!</p>
            </div>
          )}
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <div className="bg-[#003399] rounded-lg p-8 text-white">
            <h3 className="text-2xl font-bold mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              Never Miss a {category} Tender in {countryName}
            </h3>
            <p className="text-lg mb-6 opacity-90">
              Get real-time alerts for {category} government tenders in {countryName} matching your business profile.
            </p>
            <Link
              href="/pricing"
              className="inline-flex items-center px-8 py-3 border border-transparent text-lg font-medium rounded-lg text-[#003399] bg-[#FFCC00] hover:bg-[#FFD700] transition-colors"
            >
              Start Free Trial
            </Link>
          </div>
        </div>

        {/* Related Pages */}
        <div className="mt-12">
          <h3 className="text-xl font-bold text-gray-900 mb-6" style={{fontFamily: 'Manrope, sans-serif'}}>
            Explore Related Opportunities
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link
              href={`/seo/countries/${countryCode}`}
              className="p-4 rounded-lg border border-gray-200 hover:border-[#003399] hover:bg-blue-50 transition-colors"
            >
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-lg">{flag}</span>
                <span className="font-medium text-[#003399]">All {countryName} Tenders</span>
              </div>
              <p className="text-sm text-gray-600">View all government tenders in {countryName}</p>
            </Link>
            
            <Link
              href={`/seo/cpv-codes/72000000`}
              className="p-4 rounded-lg border border-gray-200 hover:border-[#003399] hover:bg-blue-50 transition-colors"
            >
              <div className="font-medium text-[#003399] mb-2">IT Services Tenders</div>
              <p className="text-sm text-gray-600">Information technology opportunities across Europe</p>
            </Link>
            
            <Link
              href={`/seo/value-ranges/medium`}
              className="p-4 rounded-lg border border-gray-200 hover:border-[#003399] hover:bg-blue-50 transition-colors"
            >
              <div className="font-medium text-[#003399] mb-2">Medium Value Tenders</div>
              <p className="text-sm text-gray-600">€50K - €500K government contracts</p>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
