'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import Link from 'next/link'
import { apiClient, Tender } from '@/lib/api'

// Check if Clerk is properly configured
const hasClerkKeys = typeof window !== 'undefined' && 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

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
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                {tender.title}
              </h3>
              <p className="text-gray-600 mb-3">
                {tender.summary}
              </p>
              <div className="flex items-center gap-4 text-sm text-gray-500">
                <span>Ref: {tender.tender_ref}</span>
                <span>Source: {tender.source}</span>
                <span>Country: {tender.buyer_country}</span>
                <span>Value: {tender.currency} {tender.value_amount?.toLocaleString()}</span>
              </div>
              <div className="mt-3">
                <a 
                  href={tender.url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:text-blue-800 text-sm"
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