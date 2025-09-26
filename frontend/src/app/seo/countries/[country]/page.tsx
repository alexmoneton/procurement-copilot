import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { apiClient } from '@/lib/api'
import { passesQuality, type TenderPage } from '@/lib/seo-quality'

// Country mapping for better SEO
const COUNTRY_NAMES: Record<string, string> = {
  'ES': 'Spain',
  'GB': 'United Kingdom', 
  'DE': 'Germany',
  'FR': 'France',
  'IT': 'Italy',
  'NL': 'Netherlands',
  'BE': 'Belgium',
  'AT': 'Austria',
  'DK': 'Denmark',
  'SE': 'Sweden',
  'FI': 'Finland',
  'NO': 'Norway',
  'CH': 'Switzerland',
  'PL': 'Poland',
  'CZ': 'Czech Republic',
  'HU': 'Hungary',
  'RO': 'Romania',
  'BG': 'Bulgaria',
  'HR': 'Croatia',
  'SI': 'Slovenia',
  'SK': 'Slovakia',
  'LT': 'Lithuania',
  'LV': 'Latvia',
  'EE': 'Estonia',
  'IE': 'Ireland',
  'PT': 'Portugal',
  'GR': 'Greece',
  'CY': 'Cyprus',
  'MT': 'Malta',
  'LU': 'Luxembourg'
}

const COUNTRY_FLAGS: Record<string, string> = {
  'ES': '🇪🇸',
  'GB': '🇬🇧',
  'DE': '🇩🇪',
  'FR': '🇫🇷',
  'IT': '🇮🇹',
  'NL': '🇳🇱',
  'BE': '🇧🇪',
  'AT': '🇦🇹',
  'DK': '🇩🇰',
  'SE': '🇸🇪',
  'FI': '🇫🇮',
  'NO': '🇳🇴',
  'CH': '🇨🇭',
  'PL': '🇵🇱',
  'CZ': '🇨🇿',
  'HU': '🇭🇺',
  'RO': '🇷🇴',
  'BG': '🇧🇬',
  'HR': '🇭🇷',
  'SI': '🇸🇮',
  'SK': '🇸🇰',
  'LT': '🇱🇹',
  'LV': '🇱🇻',
  'EE': '🇪🇪',
  'IE': '🇮🇪',
  'PT': '🇵🇹',
  'GR': '🇬🇷',
  'CY': '🇨🇾',
  'MT': '🇲🇹',
  'LU': '🇱🇺'
}

interface CountryPageProps {
  params: {
    country: string
  }
}

export async function generateMetadata({ params }: CountryPageProps): Promise<Metadata> {
  const countryCode = params.country.toUpperCase()
  const countryName = COUNTRY_NAMES[countryCode]
  
  if (!countryName) {
    return {
      title: 'Country Not Found - TenderPulse',
    }
  }

  // Check if page should be indexed (in production, this would query the database)
  const shouldIndex = true // This would be: await getPageIndexableStatus(`/seo/countries/${params.country}`)

  return {
    title: `${countryName} Government Tenders & EU Procurement Opportunities | TenderPulse`,
    description: `Find active government tenders and EU procurement opportunities in ${countryName}. Monitor ${countryName} public contracts worth millions with TenderPulse's real-time alerts.`,
    keywords: [
      `${countryName} government tenders`,
      `${countryName} public procurement`,
      `${countryName} EU tenders`,
      `${countryName} government contracts`,
      `${countryName} public sector opportunities`,
      `${countryName} procurement portal`,
      `${countryName} tender opportunities`,
      `${countryName} government bidding`
    ],
    robots: {
      index: shouldIndex,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
      'max-video-preview': -1,
    },
    openGraph: {
      title: `${countryName} Government Tenders & EU Procurement | TenderPulse`,
      description: `Discover active government tenders in ${countryName}. Real-time alerts for ${countryName} public procurement opportunities.`,
      type: 'website',
      locale: 'en_US',
    },
    twitter: {
      card: 'summary_large_image',
      title: `${countryName} Government Tenders | TenderPulse`,
      description: `Find ${countryName} government tenders and EU procurement opportunities.`,
    },
    alternates: {
      canonical: `https://tenderpulse.eu/seo/countries/${countryCode.toLowerCase()}`,
    },
  }
}

export async function generateStaticParams() {
  // Generate static params for all countries we have data for
  const countries = Object.keys(COUNTRY_NAMES)
  return countries.map((country) => ({
    country: country.toLowerCase(),
  }))
}

export default async function CountryPage({ params }: CountryPageProps) {
  const countryCode = params.country.toUpperCase()
  const countryName = COUNTRY_NAMES[countryCode]
  const flag = COUNTRY_FLAGS[countryCode]

  if (!countryName) {
    notFound()
  }

  // Fetch tenders for this country using SEO API
  const seoResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.tenderpulse.eu'}/api/v1/seo/tenders?country=${countryCode}&limit=20`)
  const seoTenders = seoResponse.ok ? await seoResponse.json() : []
  
  // Filter tenders for this specific country
  const tenders = seoTenders.filter((tender: any) => tender.country === countryCode)
  const totalTenders = tenders.length

  // Calculate total value
  const totalValue = tenders.reduce((sum: number, tender: any) => {
    return sum + (tender.value_amount || 0)
  }, 0)

  // Quality gate - only index if page has sufficient content
  const hasQualityContent = totalTenders >= 5 && totalValue > 0
  const shouldIndex = hasQualityContent

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
    <>
      {/* Noindex gate - only index if quality content */}
      {!shouldIndex && (
        <head>
          <meta name="robots" content="noindex,follow" />
        </head>
      )}
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
            <h1 className="text-4xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              {flag} {countryName} Government Tenders
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Discover active government procurement opportunities in {countryName}. 
              Monitor {countryName} public contracts and EU tenders in real-time.
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">{totalTenders}</div>
            <div className="text-gray-600">Active Tenders</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">
              {formatCurrency(totalValue)}
            </div>
            <div className="text-gray-600">Total Value</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">24/7</div>
            <div className="text-gray-600">Monitoring</div>
          </div>
        </div>

        {/* Recent Tenders */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>
              Recent {countryName} Government Tenders
            </h2>
          </div>
          
          <div className="divide-y divide-gray-200">
            {tenders.map((tender) => (
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
                    
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Buyer:</span> {tender.buyer_name || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Deadline:</span> {tender.deadline ? formatDate(tender.deadline) : 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Value:</span> {tender.value_amount ? formatCurrency(tender.value_amount) : 'N/A'}
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
              <p>No active tenders found for {countryName} at the moment.</p>
              <p className="mt-2">Check back soon for new opportunities!</p>
            </div>
          )}
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <div className="bg-[#003399] rounded-lg p-8 text-white">
            <h3 className="text-2xl font-bold mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              Never Miss a {countryName} Tender Again
            </h3>
            <p className="text-lg mb-6 opacity-90">
              Get real-time alerts for {countryName} government tenders matching your business profile.
            </p>
            <Link
              href="/pricing"
              className="inline-flex items-center px-8 py-3 border border-transparent text-lg font-medium rounded-lg text-[#003399] bg-[#FFCC00] hover:bg-[#FFD700] transition-colors"
            >
              Start Free Trial
            </Link>
          </div>
        </div>

        {/* Related Countries */}
        <div className="mt-12">
          <h3 className="text-xl font-bold text-gray-900 mb-6" style={{fontFamily: 'Manrope, sans-serif'}}>
            Explore Other EU Countries
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {Object.entries(COUNTRY_NAMES).slice(0, 12).map(([code, name]) => (
              <Link
                key={code}
                href={`/seo/countries/${code.toLowerCase()}`}
                className="flex items-center space-x-2 p-3 rounded-lg border border-gray-200 hover:border-[#003399] hover:bg-blue-50 transition-colors"
              >
                <span className="text-lg">{COUNTRY_FLAGS[code]}</span>
                <span className="text-sm font-medium text-gray-700">{name}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
    </>
  )
}
