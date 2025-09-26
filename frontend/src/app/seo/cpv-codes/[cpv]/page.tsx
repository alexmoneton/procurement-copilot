import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { apiClient } from '@/lib/api'

// CPV code descriptions for better SEO
const CPV_DESCRIPTIONS: Record<string, { name: string; description: string; category: string }> = {
  '72000000': {
    name: 'IT services: consulting, software development, Internet and support',
    description: 'Information technology services including consulting, software development, web services, and technical support',
    category: 'Information Technology'
  },
  '79400000': {
    name: 'Business and management consultancy and related services',
    description: 'Business consulting, management services, and related professional services',
    category: 'Consulting'
  },
  '60100000': {
    name: 'Road transport services',
    description: 'Transportation services by road including freight and passenger transport',
    category: 'Transportation'
  },
  '34600000': {
    name: 'Motor vehicles, trailers and semi-trailers',
    description: 'Motor vehicles, trailers, and related automotive equipment',
    category: 'Automotive'
  },
  '45000000': {
    name: 'Construction work',
    description: 'Construction and building work including civil engineering projects',
    category: 'Construction'
  },
  '48000000': {
    name: 'Software package and information systems',
    description: 'Software packages, information systems, and computer programs',
    category: 'Software'
  },
  '71000000': {
    name: 'Architectural, construction, engineering and inspection services',
    description: 'Architectural, construction, engineering, and inspection services',
    category: 'Engineering'
  },
  '73000000': {
    name: 'Research and development services and related consultancy services',
    description: 'Research and development services and related consultancy',
    category: 'Research & Development'
  },
  '75000000': {
    name: 'Administration, defence and social security services',
    description: 'Administration, defence, and social security services',
    category: 'Public Administration'
  },
  '80000000': {
    name: 'Education and training services',
    description: 'Education and training services including professional development',
    category: 'Education'
  },
  '85000000': {
    name: 'Health and social work services',
    description: 'Health and social work services including medical and care services',
    category: 'Healthcare'
  },
  '90000000': {
    name: 'Sewage, refuse, cleaning and environmental services',
    description: 'Environmental services including waste management and cleaning',
    category: 'Environmental'
  }
}

interface CPVPageProps {
  params: {
    cpv: string
  }
}

export async function generateMetadata({ params }: CPVPageProps): Promise<Metadata> {
  const cpvCode = params.cpv
  const cpvInfo = CPV_DESCRIPTIONS[cpvCode]
  
  if (!cpvInfo) {
    return {
      title: 'CPV Code Not Found - TenderPulse',
    }
  }

  return {
    title: `CPV ${cpvCode} Tenders: ${cpvInfo.name} | EU Government Contracts | TenderPulse`,
    description: `Find EU government tenders for CPV code ${cpvCode} - ${cpvInfo.name}. Discover ${cpvInfo.category} opportunities across Europe with TenderPulse.`,
    keywords: [
      `CPV ${cpvCode}`,
      `${cpvInfo.name}`,
      `${cpvInfo.category} tenders`,
      `EU government contracts ${cpvCode}`,
      `European procurement ${cpvCode}`,
      `${cpvInfo.category} opportunities`,
      `government tenders ${cpvCode}`,
      `public sector ${cpvInfo.category}`
    ],
    openGraph: {
      title: `CPV ${cpvCode} Tenders: ${cpvInfo.name} | TenderPulse`,
      description: `Discover EU government tenders for ${cpvInfo.name}. Real-time alerts for CPV ${cpvCode} opportunities.`,
      type: 'website',
      locale: 'en_US',
    },
    twitter: {
      card: 'summary_large_image',
      title: `CPV ${cpvCode} Tenders | TenderPulse`,
      description: `Find EU government tenders for ${cpvInfo.name}.`,
    },
    alternates: {
      canonical: `https://tenderpulse.eu/seo/cpv-codes/${cpvCode}`,
    },
  }
}

export async function generateStaticParams() {
  // Generate static params for all CPV codes we have data for
  const cpvCodes = Object.keys(CPV_DESCRIPTIONS)
  return cpvCodes.map((cpv) => ({
    cpv: cpv,
  }))
}

export default async function CPVPage({ params }: CPVPageProps) {
  const cpvCode = params.cpv
  const cpvInfo = CPV_DESCRIPTIONS[cpvCode]

  if (!cpvInfo) {
    notFound()
  }

  // Fetch tenders for this CPV code using SEO API
  const seoResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.tenderpulse.eu'}/api/v1/seo/tenders?limit=100`)
  const seoTenders = seoResponse.ok ? await seoResponse.json() : []
  
  // Filter tenders for this specific CPV code
  const tenders = seoTenders.filter((tender: any) => 
    tender.cpv_codes && tender.cpv_codes.includes(cpvCode)
  )
  const totalTenders = tenders.length

  // Calculate total value
  const totalValue = tenders.reduce((sum: number, tender: any) => {
    return sum + (tender.value_amount || 0)
  }, 0)

  // Get unique countries
  const countries = [...new Set(tenders.map((t: any) => t.buyer_country))].filter(Boolean)

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
              CPV Code: {cpvCode}
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              {cpvInfo.name}
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Discover EU government tenders for {cpvInfo.name.toLowerCase()}. 
              Find {cpvInfo.category} opportunities across Europe.
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
            <div className="text-3xl font-bold text-[#003399] mb-2">{cpvInfo.category}</div>
            <div className="text-gray-600">Category</div>
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

        {/* Recent Tenders */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>
              Recent CPV {cpvCode} Tenders
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
                          {tender.cpv_codes.map((code) => (
                            <span 
                              key={code} 
                              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                code === cpvCode 
                                  ? 'bg-[#003399] text-white' 
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                            >
                              {code}
                            </span>
                          ))}
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
              <p>No active tenders found for CPV code {cpvCode} at the moment.</p>
              <p className="mt-2">Check back soon for new opportunities!</p>
            </div>
          )}
        </div>

        {/* CTA */}
        <div className="mt-12 text-center">
          <div className="bg-[#003399] rounded-lg p-8 text-white">
            <h3 className="text-2xl font-bold mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              Get Alerts for CPV {cpvCode} Tenders
            </h3>
            <p className="text-lg mb-6 opacity-90">
              Never miss a {cpvInfo.category.toLowerCase()} opportunity. Get real-time alerts for CPV {cpvCode} tenders.
            </p>
            <Link
              href="/pricing"
              className="inline-flex items-center px-8 py-3 border border-transparent text-lg font-medium rounded-lg text-[#003399] bg-[#FFCC00] hover:bg-[#FFD700] transition-colors"
            >
              Start Free Trial
            </Link>
          </div>
        </div>

        {/* Related CPV Codes */}
        <div className="mt-12">
          <h3 className="text-xl font-bold text-gray-900 mb-6" style={{fontFamily: 'Manrope, sans-serif'}}>
            Related CPV Categories
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(CPV_DESCRIPTIONS).slice(0, 6).map(([code, info]) => (
              <Link
                key={code}
                href={`/seo/cpv-codes/${code}`}
                className="p-4 rounded-lg border border-gray-200 hover:border-[#003399] hover:bg-blue-50 transition-colors"
              >
                <div className="font-medium text-[#003399] mb-1">CPV {code}</div>
                <div className="text-sm text-gray-600 mb-2">{info.name}</div>
                <div className="text-xs text-gray-500">{info.category}</div>
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
