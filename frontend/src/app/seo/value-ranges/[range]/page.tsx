import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { apiClient } from '@/lib/api'

// Value range configurations
const VALUE_RANGES: Record<string, { 
  name: string; 
  description: string; 
  minValue: number; 
  maxValue?: number;
  category: string;
  keywords: string[];
}> = {
  'small': {
    name: 'Small Tenders (€0 - €50K)',
    description: 'Small-scale government tenders and contracts under €50,000',
    minValue: 0,
    maxValue: 50000,
    category: 'Small Contracts',
    keywords: ['small tenders', 'small contracts', 'under 50k', 'micro contracts']
  },
  'medium': {
    name: 'Medium Tenders (€50K - €500K)',
    description: 'Medium-scale government tenders and contracts between €50,000 and €500,000',
    minValue: 50000,
    maxValue: 500000,
    category: 'Medium Contracts',
    keywords: ['medium tenders', 'medium contracts', '50k to 500k', 'mid-size contracts']
  },
  'large': {
    name: 'Large Tenders (€500K - €5M)',
    description: 'Large-scale government tenders and contracts between €500,000 and €5 million',
    minValue: 500000,
    maxValue: 5000000,
    category: 'Large Contracts',
    keywords: ['large tenders', 'large contracts', '500k to 5m', 'major contracts']
  },
  'enterprise': {
    name: 'Enterprise Tenders (€5M+)',
    description: 'Enterprise-scale government tenders and contracts over €5 million',
    minValue: 5000000,
    category: 'Enterprise Contracts',
    keywords: ['enterprise tenders', 'enterprise contracts', 'over 5m', 'mega contracts']
  }
}

interface ValueRangePageProps {
  params: {
    range: string
  }
}

export async function generateMetadata({ params }: ValueRangePageProps): Promise<Metadata> {
  const rangeKey = params.range
  const rangeInfo = VALUE_RANGES[rangeKey]
  
  if (!rangeInfo) {
    return {
      title: 'Value Range Not Found - TenderPulse',
    }
  }

  return {
    title: `${rangeInfo.name} | EU Government Tenders | TenderPulse`,
    description: `Find ${rangeInfo.description}. Discover ${rangeInfo.category} opportunities across Europe with TenderPulse's real-time alerts.`,
    keywords: [
      ...rangeInfo.keywords,
      'EU government tenders',
      'European procurement',
      'government contracts',
      'public sector opportunities',
      'tender opportunities',
      'government bidding'
    ],
    openGraph: {
      title: `${rangeInfo.name} | TenderPulse`,
      description: `Discover ${rangeInfo.description}. Real-time alerts for ${rangeInfo.category} opportunities.`,
      type: 'website',
      locale: 'en_US',
    },
    twitter: {
      card: 'summary_large_image',
      title: `${rangeInfo.name} | TenderPulse`,
      description: `Find ${rangeInfo.description}.`,
    },
    alternates: {
      canonical: `https://tenderpulse.eu/seo/value-ranges/${rangeKey}`,
    },
  }
}

export async function generateStaticParams() {
  // Generate static params for all value ranges
  const ranges = Object.keys(VALUE_RANGES)
  return ranges.map((range) => ({
    range: range,
  }))
}

export default async function ValueRangePage({ params }: ValueRangePageProps) {
  const rangeKey = params.range
  const rangeInfo = VALUE_RANGES[rangeKey]

  if (!rangeInfo) {
    notFound()
  }

  // Fetch tenders for this value range
  const response = await apiClient.getTenders({ 
    min_value: rangeInfo.minValue,
    max_value: rangeInfo.maxValue,
    limit: 20 
  })

  const tenders = response.data?.tenders || []
  const totalTenders = response.data?.total || 0

  // Calculate total value
  const totalValue = tenders.reduce((sum, tender) => {
    return sum + (tender.value_amount || 0)
  }, 0)

  // Get unique countries
  const countries = [...new Set(tenders.map(t => t.buyer_country))].filter(Boolean)

  // Get unique CPV codes
  const cpvCodes = [...new Set(tenders.flatMap(t => t.cpv_codes || []))].slice(0, 10)

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

  const getCountryFlag = (countryCode: string) => {
    const flags: Record<string, string> = {
      'ES': '🇪🇸', 'GB': '🇬🇧', 'DE': '🇩🇪', 'FR': '🇫🇷', 'IT': '🇮🇹', 'NL': '🇳🇱',
      'BE': '🇧🇪', 'AT': '🇦🇹', 'DK': '🇩🇰', 'SE': '🇸🇪', 'FI': '🇫🇮', 'NO': '🇳🇴'
    }
    return flags[countryCode] || '🌍'
  }

  const getValueRangeIcon = (range: string) => {
    const icons: Record<string, string> = {
      'small': '🏢',
      'medium': '🏭',
      'large': '🏗️',
      'enterprise': '🏛️'
    }
    return icons[range] || '💰'
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
            <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 text-green-800 text-sm font-medium mb-4">
              {getValueRangeIcon(rangeKey)} {rangeInfo.category}
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              {rangeInfo.name}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              {rangeInfo.description}. Find {rangeInfo.category.toLowerCase()} opportunities across Europe.
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-12">
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
            <div className="text-3xl font-bold text-[#003399] mb-2">{countries.length}</div>
            <div className="text-gray-600">Countries</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6 text-center">
            <div className="text-3xl font-bold text-[#003399] mb-2">
              {formatCurrency(totalValue / Math.max(totalTenders, 1))}
            </div>
            <div className="text-gray-600">Avg. Value</div>
          </div>
        </div>

        {/* Countries */}
        {countries.length > 0 && (
          <div className="mb-12">
            <h3 className="text-xl font-bold text-gray-900 mb-6" style={{fontFamily: 'Manrope, sans-serif'}}>
              Available in {countries.length} Countries
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {countries.map((country) => (
                <Link
                  key={country}
                  href={`/seo/countries/${country.toLowerCase()}`}
                  className="flex items-center space-x-2 p-3 rounded-lg border border-gray-200 hover:border-[#003399] hover:bg-blue-50 transition-colors"
                >
                  <span className="text-lg">{getCountryFlag(country)}</span>
                  <span className="text-sm font-medium text-gray-700">{country}</span>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* CPV Codes */}
        {cpvCodes.length > 0 && (
          <div className="mb-12">
            <h3 className="text-xl font-bold text-gray-900 mb-6" style={{fontFamily: 'Manrope, sans-serif'}}>
              Popular CPV Codes
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              {cpvCodes.map((cpv) => (
                <Link
                  key={cpv}
                  href={`/seo/cpv-codes/${cpv}`}
                  className="p-3 rounded-lg border border-gray-200 hover:border-[#003399] hover:bg-blue-50 transition-colors text-center"
                >
                  <div className="font-medium text-[#003399]">{cpv}</div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Recent Tenders */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>
              Recent {rangeInfo.name}
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
                    
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">Buyer:</span> {tender.buyer_name || 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Country:</span> {getCountryFlag(tender.buyer_country)} {tender.buyer_country}
                      </div>
                      <div>
                        <span className="font-medium">Deadline:</span> {tender.deadline_date ? formatDate(tender.deadline_date) : 'N/A'}
                      </div>
                      <div>
                        <span className="font-medium">Value:</span> {tender.value_amount ? formatCurrency(tender.value_amount) : 'N/A'}
                      </div>
                    </div>
                    
                    {tender.cpv_codes && tender.cpv_codes.length > 0 && (
                      <div className="mt-2">
                        <span className="font-medium text-sm text-gray-600">CPV Codes:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {tender.cpv_codes.slice(0, 3).map((code) => (
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
              <p>No active tenders found for {rangeInfo.name.toLowerCase()} at the moment.</p>
              <p className="mt-2">Check back soon for new opportunities!</p>
            </div>
          )}
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <div className="bg-[#003399] rounded-lg p-8 text-white">
            <h3 className="text-2xl font-bold mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              Get Alerts for {rangeInfo.name}
            </h3>
            <p className="text-lg mb-6 opacity-90">
              Never miss a {rangeInfo.category.toLowerCase()} opportunity. Get real-time alerts for {rangeInfo.name.toLowerCase()}.
            </p>
            <Link
              href="/pricing"
              className="inline-flex items-center px-8 py-3 border border-transparent text-lg font-medium rounded-lg text-[#003399] bg-[#FFCC00] hover:bg-[#FFD700] transition-colors"
            >
              Start Free Trial
            </Link>
          </div>
        </div>

        {/* Related Value Ranges */}
        <div className="mt-12">
          <h3 className="text-xl font-bold text-gray-900 mb-6" style={{fontFamily: 'Manrope, sans-serif'}}>
            Other Value Ranges
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(VALUE_RANGES).map(([key, info]) => (
              <Link
                key={key}
                href={`/seo/value-ranges/${key}`}
                className={`p-4 rounded-lg border transition-colors ${
                  key === rangeKey 
                    ? 'border-[#003399] bg-blue-50' 
                    : 'border-gray-200 hover:border-[#003399] hover:bg-blue-50'
                }`}
              >
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-lg">{getValueRangeIcon(key)}</span>
                  <div className="font-medium text-[#003399]">{info.category}</div>
                </div>
                <div className="text-sm text-gray-600">{info.name}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
