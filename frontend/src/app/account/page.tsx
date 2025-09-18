'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import Link from 'next/link'
import { UserIcon, CreditCardIcon, BellIcon, CheckIcon } from '@heroicons/react/24/outline'
import { apiClient } from '@/lib/api'

// Check if Clerk is properly configured
const hasClerkKeys = typeof window !== 'undefined' && 
  process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

interface UserPlan {
  id: string
  name: string
  filters: number
  status: 'active' | 'canceled' | 'past_due'
}

function AccountPageContent() {
  const { user } = useUser()
  const [plan, setPlan] = useState<UserPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [billingLoading, setBillingLoading] = useState(false)

  useEffect(() => {
    if (user?.emailAddresses?.[0]?.emailAddress) {
      apiClient.setUserEmail(user.emailAddresses[0].emailAddress)
      // Simulate loading user plan
      setTimeout(() => {
        setPlan({
          id: 'starter',
          name: 'Starter',
          filters: 1,
          status: 'active'
        })
        setLoading(false)
      }, 1000)
    }
  }, [user])

  const handleBillingPortal = async () => {
    setBillingLoading(true)
    try {
      const response = await apiClient.getBillingPortal()
      if (response.data?.url) {
        window.location.href = response.data.url
      }
    } catch (error) {
      console.error('Error accessing billing portal:', error)
    } finally {
      setBillingLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003399] mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your account...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-4">
              <img src="/logo.svg" alt="TenderPulse" className="h-8 w-auto" />
              <div>
                <h1 className="text-xl font-bold text-[#003399]" style={{fontFamily: 'Manrope, sans-serif'}}>Account Settings</h1>
                <p className="text-sm text-gray-600">Manage your TenderPulse subscription</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/app" className="text-sm font-medium text-gray-600 hover:text-[#003399] transition-colors">
                ← Back to Dashboard
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-4xl px-6 py-12 lg:px-8">
        <div className="space-y-8">
          {/* Profile section */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="h-12 w-12 bg-[#003399]/10 rounded-full flex items-center justify-center">
                <UserIcon className="h-6 w-6 text-[#003399]" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>Profile</h2>
                <p className="text-sm text-gray-600">Your account information</p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                <div className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded-lg">
                  {user?.emailAddresses?.[0]?.emailAddress || 'Not available'}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Account Status</label>
                <div className="text-sm">
                  <span className="inline-flex items-center gap-2 rounded-full bg-green-100 px-3 py-1 text-green-800">
                    <span className="h-2 w-2 rounded-full bg-green-500"></span>
                    Active
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Subscription section */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="h-12 w-12 bg-[#FFCC00]/20 rounded-full flex items-center justify-center">
                <CreditCardIcon className="h-6 w-6 text-[#003399]" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>Subscription</h2>
                <p className="text-sm text-gray-600">Manage your billing and plan</p>
              </div>
            </div>
            
            {plan ? (
              <div className="space-y-6">
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Current Plan</label>
                    <div className="text-lg font-semibold text-[#003399]">{plan.name}</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Saved Filters</label>
                    <div className="text-lg font-semibold text-gray-900">{plan.filters} filters</div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                    <div className="text-lg font-semibold text-green-600 capitalize">{plan.status}</div>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4">
                  <button
                    onClick={handleBillingPortal}
                    disabled={billingLoading}
                    className="bg-[#003399] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#002266] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {billingLoading ? 'Loading...' : 'Manage Billing'}
                  </button>
                  <Link
                    href="/pricing"
                    className="border-2 border-[#003399] text-[#003399] px-6 py-3 rounded-lg font-medium hover:bg-[#003399] hover:text-white transition-colors text-center"
                  >
                    Upgrade Plan
                  </Link>
                </div>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">No active subscription</p>
                <Link
                  href="/pricing"
                  className="bg-[#FFCC00] text-[#003399] px-6 py-3 rounded-lg font-semibold hover:bg-[#FFD700] transition-colors"
                >
                  Choose a Plan
                </Link>
              </div>
            )}
          </div>

          {/* Preferences section */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <div className="flex items-center gap-4 mb-6">
              <div className="h-12 w-12 bg-[#003399]/10 rounded-full flex items-center justify-center">
                <BellIcon className="h-6 w-6 text-[#003399]" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>Preferences</h2>
                <p className="text-sm text-gray-600">Configure your alert settings</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between py-4 border-b border-gray-100">
                <div>
                  <h3 className="font-medium text-gray-900">Email Notifications</h3>
                  <p className="text-sm text-gray-600">Receive daily tender alerts</p>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-[#003399] focus:ring-[#003399] border-gray-300 rounded"
                  />
                </div>
              </div>
              <div className="flex items-center justify-between py-4 border-b border-gray-100">
                <div>
                  <h3 className="font-medium text-gray-900">Weekly Summary</h3>
                  <p className="text-sm text-gray-600">Get a weekly digest of opportunities</p>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="h-4 w-4 text-[#003399] focus:ring-[#003399] border-gray-300 rounded"
                  />
                </div>
              </div>
              <div className="flex items-center justify-between py-4">
                <div>
                  <h3 className="font-medium text-gray-900">Product Updates</h3>
                  <p className="text-sm text-gray-600">Notifications about new features</p>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-[#003399] focus:ring-[#003399] border-gray-300 rounded"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Usage section */}
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-6" style={{fontFamily: 'Manrope, sans-serif'}}>Usage This Month</h2>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              <div className="text-center p-6 bg-gray-50 rounded-xl">
                <div className="text-2xl font-bold text-[#003399]">47</div>
                <div className="text-sm text-gray-600">Alerts Sent</div>
              </div>
              <div className="text-center p-6 bg-gray-50 rounded-xl">
                <div className="text-2xl font-bold text-[#003399]">1</div>
                <div className="text-sm text-gray-600">Active Filters</div>
              </div>
              <div className="text-center p-6 bg-gray-50 rounded-xl">
                <div className="text-2xl font-bold text-[#003399]">€2.1M</div>
                <div className="text-sm text-gray-600">Opportunities Value</div>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-gray-900">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src="/logo.svg" alt="TenderPulse" className="h-8 w-auto" />
              <span className="text-xl font-bold text-white">TenderPulse</span>
            </div>
            <p className="text-sm text-gray-400">
              © 2025 TenderPulse. All rights reserved.
            </p>
          </div>
          <div className="mt-8 border-t border-gray-800 pt-8">
            <p className="text-xs text-gray-500 text-center">
              TenderPulse is an independent service and is not affiliated with the European Union or its institutions.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}

// Main component with Clerk check
export default function AccountPage() {
  if (!hasClerkKeys) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Account Settings</h1>
          <p className="text-gray-600 mb-8">Authentication is not configured</p>
          <Link href="/" className="bg-[#003399] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#002266] transition-colors">
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  return <AccountPageContent />
}