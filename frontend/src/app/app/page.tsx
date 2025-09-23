'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { apiClient, Tender } from '@/lib/api'

// Check if Clerk is properly configured
const hasClerkKeys = typeof window !== 'undefined' && 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

// Helper function to format dates from TED API
function formatDate(dateString: string): string {
  if (!dateString) return 'Not specified'
  
  try {
    // Handle TED API date formats like "2015-10-07+02:00" or "2025-11-02"
    const cleanDate = dateString.split('+')[0].split('T')[0] // Remove timezone and time
    const date = new Date(cleanDate)
    
    if (isNaN(date.getTime())) {
      return 'Invalid Date'
    }
    
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  } catch (error) {
    console.warn('Error formatting date:', dateString, error)
    return 'Invalid Date'
  }
}

function DashboardPageContent() {
  const [tenders, setTenders] = useState<Tender[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Simple data loading without complex dependencies
    loadData()
  }, [])

  const loadData = async () => {
    try {
      console.log('🔍 Loading tenders...')
      const response = await apiClient.getTenders({ limit: 100 })
      
      if (response.error) {
        setError(response.error)
      } else if (response.data?.tenders) {
        console.log('✅ Loaded tenders:', response.data.tenders.length)
        setTenders(response.data.tenders)
      } else {
        setError('No tenders received from API')
      }
    } catch (err) {
      console.error('❌ Error:', err)
      setError('Failed to load data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <div className="text-red-600 text-lg mb-4">{error}</div>
        <button 
          onClick={() => {
            setError(null)
            loadData()
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  if (tenders.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-600 text-lg">No tenders found</div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center gap-4">
            <Image src="/logo.svg" alt="TenderPulse" width={32} height={32} className="h-8 w-auto" />
            <div>
              <h1 className="text-xl font-bold text-[#003399]" style={{fontFamily: 'Manrope, sans-serif'}}>TenderPulse</h1>
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium" style={{backgroundColor: 'rgba(0, 51, 153, 0.1)', color: '#003399'}}>
                Live TED Data • Real-time EU procurement notices
              </span>
            </div>
          </div>
          <Link href="/" className="text-sm font-medium text-gray-600 hover:text-[#003399] transition-colors">
            ← Back to Home
          </Link>
        </div>
      </div>

      {/* Simple Tenders List */}
      <div>
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-gray-900">
            Real TED Tenders ({tenders.length})
          </h2>
          <div className="flex gap-3">
            <Link 
              href="/profile"
              className="px-4 py-2 rounded-lg text-white font-medium text-sm transition-all duration-300 hover:transform hover:translate-y-[-1px] hover:shadow-lg"
              style={{
                background: 'linear-gradient(135deg, #003399, #0052CC)',
              }}
            >
              ⚙️ Setup Profile
            </Link>
            <Link 
              href="/alerts"
              className="px-4 py-2 rounded-lg text-white font-medium text-sm transition-all duration-300 hover:transform hover:translate-y-[-1px] hover:shadow-lg"
              style={{
                background: 'linear-gradient(135deg, #FFCC00, #FFB000)',
                color: '#003399'
              }}
            >
              🔔 Setup Smart Alerts
            </Link>
          </div>
        </div>
        <div className="grid gap-6">
          {tenders.map((tender) => (
            <div 
              key={tender.id} 
              className={`relative p-6 rounded-xl transition-all duration-300 hover:transform hover:translate-y-[-2px] hover:shadow-xl border-l-4 ${
                tender.smart_score && tender.smart_score >= 70 ? 'bg-gradient-to-r from-white to-green-50 border-l-green-500' :
                tender.smart_score && tender.smart_score >= 50 ? 'bg-gradient-to-r from-white to-yellow-50 border-l-yellow-500' :
                tender.smart_score ? 'bg-gradient-to-r from-white to-red-50 border-l-red-500' :
                'bg-white border-l-gray-300'
              }`}
              style={{
                boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
                background: tender.smart_score && tender.smart_score >= 70 ? 'linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%)' :
                           tender.smart_score && tender.smart_score >= 50 ? 'linear-gradient(135deg, #ffffff 0%, #fffbeb 100%)' :
                           tender.smart_score ? 'linear-gradient(135deg, #ffffff 0%, #fef2f2 100%)' :
                           'white'
              }}
            >
              {tender.smart_score ? (
                <div 
                  className="absolute top-4 right-4 px-3 py-1 rounded-full text-white font-semibold text-sm"
                  style={{
                    background: tender.smart_score >= 70 ? 'linear-gradient(135deg, #10b981, #059669)' :
                               tender.smart_score >= 50 ? 'linear-gradient(135deg, #f59e0b, #d97706)' :
                               'linear-gradient(135deg, #ef4444, #dc2626)'
                  }}
                >
                  {tender.smart_score}% Match
                </div>
              ) : (
                <div 
                  className="absolute top-4 right-4 px-2 py-1 rounded-full text-gray-600 font-medium text-xs bg-gray-100 border border-gray-200 max-w-48"
                >
                  Set up profile to see match score
                </div>
              )}
              
              <div className="pr-32 mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2 leading-tight">
                  {tender.title}
                </h3>
              </div>
              
              <p className="text-gray-600 mb-3">
                {tender.summary}
              </p>
              
              {(tender.competition_level || tender.deadline_urgency) ? (
                <div className="p-4 rounded-lg mb-4 border" style={{
                  background: 'linear-gradient(135deg, #eff6ff, #dbeafe)',
                  borderColor: '#bfdbfe'
                }}>
                  <h4 className="font-semibold text-sm mb-2" style={{color: '#1e40af'}}>
                    🎯 Why You&apos;ll Win:
                  </h4>
                  <ul className="space-y-1">
                    {tender.competition_level && (
                      <li className="text-sm text-gray-700 pl-5 relative">
                        <span className="absolute left-0 text-green-600 font-bold">✓</span>
                        Competition: {tender.competition_level}
                      </li>
                    )}
                    {tender.deadline_urgency && (
                      <li className="text-sm text-gray-700 pl-5 relative">
                        <span className="absolute left-0 text-green-600 font-bold">✓</span>
                        Strategy: {tender.deadline_urgency}
                      </li>
                    )}
                    <li className="text-sm text-gray-700 pl-5 relative">
                      <span className="absolute left-0 text-green-600 font-bold">✓</span>
                      Perfect size match for your capacity
                    </li>
                  </ul>
                </div>
              ) : (
                <div className="p-4 rounded-lg mb-4 border bg-gray-50 border-gray-200">
                  <h4 className="font-semibold text-sm mb-2 text-gray-600">
                    🎯 Personalized Analysis:
                  </h4>
                  <p className="text-sm text-gray-600">
                    Complete your profile to see personalized competition analysis, deadline strategies, and winning recommendations tailored to your company.
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-500 mb-2">
                <div>
                  <span className="font-medium">Ref:</span> {tender.tender_ref}
                </div>
                <div>
                  <span className="font-medium">Source:</span> {tender.source}
                </div>
                <div>
                  <span className="font-medium">Country:</span> {tender.buyer_country}
                </div>
                <div>
                  <span className="font-medium">Value:</span> {tender.currency} {tender.value_amount?.toLocaleString()}
                </div>
                <div>
                  <span className="font-medium">Published:</span> {formatDate(tender.publication_date)}
                </div>
                <div>
                  <span className="font-medium">Deadline:</span> {tender.deadline_date ? formatDate(tender.deadline_date) : 'Not specified'}
                </div>
                <div className="col-span-2">
                  <span className="font-medium">Buyer:</span> {tender.buyer_name || 'Not specified'}
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <a 
                  href={tender.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="px-4 py-2 rounded-lg text-white font-medium text-sm transition-all duration-300 hover:transform hover:translate-y-[-1px] hover:shadow-lg"
                  style={{
                    background: 'linear-gradient(135deg, #003399, #0052CC)',
                  }}
                >
                  View Full Tender →
                </a>
                {tender.smart_score && tender.smart_score >= 60 && (
                  <button 
                    className="px-4 py-2 rounded-lg font-medium text-sm transition-all duration-300 hover:transform hover:translate-y-[-1px]"
                    style={{
                      background: 'linear-gradient(135deg, #FFCC00, #FFB000)',
                      color: '#003399',
                      border: 'none'
                    }}
                  >
                    Get Response Kit
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  if (!hasClerkKeys) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Dashboard</h1>
          <p className="text-gray-600">Authentication is not configured. Please set up Clerk to access the dashboard.</p>
        </div>
      </div>
    )
  }

  return <DashboardPageContent />
}