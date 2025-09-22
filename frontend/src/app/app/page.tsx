'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import Link from 'next/link'
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
  const { user } = useUser()
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
      const response = await apiClient.getTenders({ limit: 10 })
      
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
            <img src="/logo.svg" alt="TenderPulse" className="h-8 w-auto" />
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
        <h2 className="text-2xl font-semibold text-gray-900 mb-4">
          Real TED Tenders ({tenders.length})
        </h2>
        <div className="grid gap-4">
          {tenders.map((tender) => (
            <div key={tender.id} className="bg-white p-6 rounded-lg shadow border border-gray-200">
              <div className="flex justify-between items-start mb-3">
                <h3 className="text-lg font-medium text-gray-900 flex-1">
                  {tender.title}
                </h3>
                {tender.smart_score && (
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ml-3 ${
                    tender.smart_score >= 70 ? 'bg-green-100 text-green-800' :
                    tender.smart_score >= 50 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {tender.smart_score}% Match
                  </span>
                )}
              </div>
              
              <p className="text-gray-600 mb-3">
                {tender.summary}
              </p>
              
              {tender.competition_level && (
                <div className="bg-blue-50 p-3 rounded-lg mb-3">
                  <div className="text-sm">
                    <span className="font-medium text-blue-900">Competition:</span> 
                    <span className="text-blue-700 ml-1">{tender.competition_level}</span>
                  </div>
                  {tender.deadline_urgency && (
                    <div className="text-sm mt-1">
                      <span className="font-medium text-blue-900">Strategy:</span> 
                      <span className="text-blue-700 ml-1">{tender.deadline_urgency}</span>
                    </div>
                  )}
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
              <div className="mt-3">
                <a 
                  href={tender.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                >
                  View on TED →
                </a>
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