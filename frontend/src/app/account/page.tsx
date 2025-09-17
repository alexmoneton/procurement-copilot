'use client'

import { useState, useEffect } from 'react'
import { useUser } from '@clerk/nextjs'
import { UserIcon, CreditCardIcon, BellIcon } from '@heroicons/react/24/outline'
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
      // In a real app, you'd fetch the user's plan from your backend
      // For now, we'll simulate a plan
      setTimeout(() => {
        setPlan({
          id: 'pro_199',
          name: 'Pro',
          filters: 5,
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
      } else {
        console.error('Failed to get billing portal:', response.error)
      }
    } catch (error) {
      console.error('Error getting billing portal:', error)
    } finally {
      setBillingLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Account Settings</h1>
            </div>
            <div className="flex items-center">
              <span className="text-sm text-gray-500">
                {user?.emailAddresses?.[0]?.emailAddress}
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Profile Information */}
          <div className="lg:col-span-2">
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  Profile Information
                </h3>
                <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Email address</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.emailAddresses?.[0]?.emailAddress}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Full name</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.fullName || 'Not provided'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Account created</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.createdAt ? new Date(user.createdAt).toLocaleDateString() : 'Unknown'}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-gray-500">Last sign in</dt>
                    <dd className="mt-1 text-sm text-gray-900">
                      {user?.lastSignInAt ? new Date(user.lastSignInAt).toLocaleDateString() : 'Unknown'}
                    </dd>
                  </div>
                </dl>
              </div>
            </div>
          </div>

          {/* Plan Information */}
          <div className="lg:col-span-1">
            <div className="bg-white shadow rounded-lg">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  Current Plan
                </h3>
                {plan ? (
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <CreditCardIcon className="h-8 w-8 text-blue-600" />
                        </div>
                        <div className="ml-3">
                          <p className="text-sm font-medium text-gray-900">{plan.name}</p>
                          <p className="text-sm text-gray-500">
                            {plan.filters} saved filters
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        plan.status === 'active' 
                          ? 'bg-green-100 text-green-800'
                          : plan.status === 'canceled'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}>
                        {plan.status === 'active' ? 'Active' : 
                         plan.status === 'canceled' ? 'Canceled' : 'Past Due'}
                      </span>
                    </div>
                    <button
                      onClick={handleBillingPortal}
                      disabled={billingLoading}
                      className="w-full bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {billingLoading ? 'Loading...' : 'Manage Billing'}
                    </button>
                  </div>
                ) : (
                  <div className="text-center">
                    <p className="text-sm text-gray-500 mb-4">No active plan</p>
                    <a
                      href="/pricing"
                      className="w-full bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 inline-block"
                    >
                      Choose a Plan
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Notification Settings */}
            <div className="bg-white shadow rounded-lg mt-6">
              <div className="px-4 py-5 sm:p-6">
                <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                  Notification Settings
                </h3>
                <div className="space-y-4">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <BellIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Email notifications</p>
                      <p className="text-sm text-gray-500">Receive tender alerts via email</p>
                    </div>
                    <div className="ml-auto">
                      <button
                        type="button"
                        className="bg-blue-600 relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2"
                        role="switch"
                        aria-checked="true"
                      >
                        <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Usage Statistics */}
        <div className="mt-8">
          <div className="bg-white shadow rounded-lg">
            <div className="px-4 py-5 sm:p-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                Usage This Month
              </h3>
              <dl className="grid grid-cols-1 gap-5 sm:grid-cols-3">
                <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <BellIcon className="h-6 w-6 text-gray-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">
                            Alerts Sent
                          </dt>
                          <dd className="text-lg font-medium text-gray-900">24</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <UserIcon className="h-6 w-6 text-gray-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">
                            Tenders Found
                          </dt>
                          <dd className="text-lg font-medium text-gray-900">156</dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-gray-50 overflow-hidden shadow rounded-lg">
                  <div className="p-5">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <CreditCardIcon className="h-6 w-6 text-gray-400" />
                      </div>
                      <div className="ml-5 w-0 flex-1">
                        <dl>
                          <dt className="text-sm font-medium text-gray-500 truncate">
                            Filters Used
                          </dt>
                          <dd className="text-lg font-medium text-gray-900">
                            {plan ? `${plan.filters}/5` : '0/0'}
                          </dd>
                        </dl>
                      </div>
                    </div>
                  </div>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function AccountPage() {
  // Only render account page when Clerk is properly configured
  if (!hasClerkKeys) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900">Account</h1>
            <p className="mt-4 text-lg text-gray-600">
              Authentication is not configured. Please set up Clerk to access your account.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return <AccountPageContent />
}
