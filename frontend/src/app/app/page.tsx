'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import Link from 'next/link'
import { PlusIcon, CalendarIcon, BellIcon } from '@heroicons/react/24/outline'
import { apiClient, Tender, SavedFilter } from '@/lib/api'
import { formatDate, formatCurrency, getDeadlineStatus, getDeadlineColor, getSourceColor } from '@/lib/utils'
import { CreateFilterModal } from '@/components/CreateFilterModal'

// Check if Clerk is properly configured
const hasClerkKeys = typeof window !== 'undefined' && 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

function DashboardPageContent() {
  const { user } = useUser()
  const [tenders, setTenders] = useState<Tender[]>([])
  const [filters, setFilters] = useState<SavedFilter[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)

  useEffect(() => {
    if (user?.emailAddresses?.[0]?.emailAddress) {
      apiClient.setUserEmail(user.emailAddresses[0].emailAddress)
      loadData()
    }
  }, [user])

  const loadData = async () => {
    setLoading(true)
    try {
      const [tendersResponse, filtersResponse] = await Promise.all([
        apiClient.getTenders({ limit: 50 }),
        apiClient.getSavedFilters()
      ])

      if (tendersResponse.data) {
        setTenders(tendersResponse.data.tenders)
      }
      if (filtersResponse.data) {
        setFilters(filtersResponse.data)
      }
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterCreated = () => {
    setShowCreateModal(false)
    loadData() // Reload filters
  }

  const upcomingDeadlines = tenders
    .filter(tender => tender.deadline_date)
    .sort((a, b) => new Date(a.deadline_date!).getTime() - new Date(b.deadline_date!).getTime())
    .slice(0, 5)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>Dashboard</h1>
            <p className="mt-2 text-sm text-gray-700">
              Welcome back! Here&apos;s what&apos;s happening with your tender monitoring.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium" style={{backgroundColor: 'rgba(0, 51, 153, 0.1)', color: '#003399'}}>
              139+ active EU tenders • €800M+ value
            </span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card-eu">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BellIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Active Filters
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">{filters.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="card-eu">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CalendarIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    New Tenders
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">{tenders.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="card-eu">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CalendarIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Upcoming Deadlines
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">{upcomingDeadlines.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
        <div className="card-eu">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BellIcon className="h-6 w-6 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Alerts This Week
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">12</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* New Tenders Feed */}
        <div className="lg:col-span-2">
          <div className="card-eu">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                New Tenders
              </h3>
              {tenders.length === 0 ? (
                <div className="text-center py-12">
                  <BellIcon className="mx-auto h-12 w-12 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No tenders found</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Create a filter to start receiving tender alerts.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {tenders.slice(0, 10).map((tender) => (
                    <div key={tender.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="text-sm font-medium text-gray-900">
                            <a
                              href={tender.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="hover:text-blue-600"
                            >
                              {tender.title}
                            </a>
                          </h4>
                          <p className="mt-1 text-sm text-gray-500">
                            {tender.buyer_name} • {tender.buyer_country}
                          </p>
                          {tender.summary && (
                            <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                              {tender.summary}
                            </p>
                          )}
                          <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500">
                            <span>Published: {formatDate(tender.publication_date)}</span>
                            {tender.deadline_date && (
                              <span>Deadline: {formatDate(tender.deadline_date)}</span>
                            )}
                            {tender.value_amount && (
                              <span>Value: {formatCurrency(tender.value_amount, tender.currency)}</span>
                            )}
                          </div>
                        </div>
                        <div className="ml-4 flex flex-col items-end space-y-2">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getSourceColor(tender.source)}`}>
                            {tender.source}
                          </span>
                          {tender.deadline_date && (
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getDeadlineColor(getDeadlineStatus(tender.deadline_date))}`}>
                              {getDeadlineStatus(tender.deadline_date)}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Saved Filters */}
          <div className="card-eu">
            <div className="px-4 py-5 sm:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg leading-6 font-medium text-gray-900">
                  Saved Filters
                </h3>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="btn-primary inline-flex items-center px-3 py-2 text-sm leading-4 font-medium rounded-md"
                >
                  <PlusIcon className="h-4 w-4 mr-1" />
                  Create
                </button>
              </div>
              {filters.length === 0 ? (
                <div className="text-center py-6">
                  <BellIcon className="mx-auto h-8 w-8 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No filters yet</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Create your first filter to start monitoring tenders.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filters.map((filter) => (
                    <div key={filter.id} className="border border-gray-200 rounded-lg p-3">
                      <h4 className="text-sm font-medium text-gray-900">{filter.name}</h4>
                      <p className="text-xs text-gray-500 mt-1">
                        {filter.keywords.length} keywords • {filter.countries.length} countries
                      </p>
                      <p className="text-xs text-gray-500">
                        {filter.notify_frequency} alerts
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Upcoming Deadlines */}
          <div className="card-eu">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Upcoming Deadlines
              </h3>
              {upcomingDeadlines.length === 0 ? (
                <div className="text-center py-6">
                  <CalendarIcon className="mx-auto h-8 w-8 text-gray-400" />
                  <h3 className="mt-2 text-sm font-medium text-gray-900">No upcoming deadlines</h3>
                  <p className="mt-1 text-sm text-gray-500">
                    Check back later for new tender deadlines.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {upcomingDeadlines.map((tender) => (
                    <div key={tender.id} className="border border-gray-200 rounded-lg p-3">
                      <h4 className="text-sm font-medium text-gray-900 line-clamp-2">
                        {tender.title}
                      </h4>
                      <p className="text-xs text-gray-500 mt-1">
                        {tender.buyer_name} • {tender.buyer_country}
                      </p>
                      <p className="text-xs text-gray-500">
                        Deadline: {formatDate(tender.deadline_date!)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Create Filter Modal */}
      {showCreateModal && (
        <CreateFilterModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={handleFilterCreated}
        />
      )}
    </div>
  )
}

export default function DashboardPage() {
  // Only render dashboard when Clerk is properly configured
  if (!hasClerkKeys) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-100">
          <div className="mx-auto max-w-7xl px-6 lg:px-8">
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
        </header>
        
        {/* Main content */}
        <div className="flex items-center justify-center py-20">
          <div className="text-center max-w-md">
            <div className="mb-8">
              <div className="mx-auto h-16 w-16 bg-[#003399]/10 rounded-full flex items-center justify-center">
                <span className="text-2xl">🔐</span>
              </div>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              Sign in to access your dashboard
            </h2>
            <p className="text-gray-600 mb-8">
              View 139+ active EU procurement opportunities and manage your tender alerts.
            </p>
            <div className="space-y-4">
              <Link href="/" className="block bg-[#FFCC00] text-[#003399] px-6 py-3 rounded-lg font-semibold hover:bg-[#FFD700] transition-colors">
                Sign Up for Free Trial
              </Link>
              <Link href="/" className="block text-sm font-medium text-gray-600 hover:text-[#003399] transition-colors">
                Back to Home
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return <DashboardPageContent />
}
