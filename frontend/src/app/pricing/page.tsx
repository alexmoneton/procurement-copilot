'use client'

import { useState } from 'react'
import Link from 'next/link'
import { CheckIcon } from '@heroicons/react/24/outline'
import { SignUpButton } from '@clerk/nextjs'
import { PLAN_OPTIONS } from '@/lib/utils'
import { apiClient } from '@/lib/api'

// Check if Clerk is properly configured
const hasClerkKeys = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null)

  const handleSelectPlan = async (planId: string) => {
    setLoading(planId)
    try {
      const response = await apiClient.createCheckoutSession(planId)
      if (response.data?.url) {
        window.location.href = response.data.url
      } else {
        console.error('Failed to create checkout session:', response.error)
      }
    } catch (error) {
      console.error('Error creating checkout session:', error)
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="bg-white">
      {/* Header */}
      <header className="absolute inset-x-0 top-0 z-50">
        <nav className="flex items-center justify-between p-6 lg:px-8" aria-label="Global">
          <div className="flex lg:flex-1">
            <Link href="/" className="-m-1.5 p-1.5">
              <span className="text-2xl font-bold text-blue-600">Procurement Copilot</span>
            </Link>
          </div>
          <div className="flex lg:flex-1 lg:justify-end">
            <Link href="/" className="text-sm font-semibold leading-6 text-gray-900 hover:text-blue-600">
              Back to home
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero section */}
      <div className="pt-24 pb-12 sm:pt-32 sm:pb-16">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h1 className="text-base font-semibold leading-7 text-blue-600">Pricing</h1>
            <p className="mt-2 text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
              Choose the plan that&apos;s right for you
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Start with a free trial, then choose the plan that fits your business needs. 
              All plans include our core monitoring and alerting features.
            </p>
          </div>
        </div>
      </div>

      {/* Pricing cards */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 pb-24">
        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {PLAN_OPTIONS.map((plan) => (
            <div
              key={plan.id}
              className={`rounded-3xl p-8 ring-1 ${
                plan.id === 'pro_199'
                  ? 'ring-blue-600 bg-blue-50'
                  : 'ring-gray-200 bg-white'
              }`}
            >
              <div className="flex items-center justify-between gap-x-4">
                <h3 className={`text-lg font-semibold leading-8 ${
                  plan.id === 'pro_199' ? 'text-blue-600' : 'text-gray-900'
                }`}>
                  {plan.name}
                </h3>
                {plan.id === 'pro_199' && (
                  <p className="rounded-full bg-blue-600/10 px-2.5 py-1 text-xs font-semibold leading-5 text-blue-600">
                    Most popular
                  </p>
                )}
              </div>
              <p className="mt-4 text-sm leading-6 text-gray-600">{plan.description}</p>
              <p className="mt-6 flex items-baseline gap-x-1">
                <span className={`text-4xl font-bold tracking-tight ${
                  plan.id === 'pro_199' ? 'text-blue-600' : 'text-gray-900'
                }`}>
                  €{plan.price}
                </span>
                <span className="text-sm font-semibold leading-6 text-gray-600">/{plan.interval}</span>
              </p>
              <ul role="list" className="mt-8 space-y-3 text-sm leading-6 text-gray-600">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex gap-x-3">
                    <CheckIcon className={`h-6 w-5 flex-none ${
                      plan.id === 'pro_199' ? 'text-blue-600' : 'text-gray-400'
                    }`} aria-hidden="true" />
                    {feature}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => handleSelectPlan(plan.id)}
                disabled={loading === plan.id}
                className={`mt-8 block w-full rounded-md px-3 py-2 text-center text-sm font-semibold leading-6 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 ${
                  plan.id === 'pro_199'
                    ? 'bg-blue-600 text-white shadow-sm hover:bg-blue-500 focus-visible:outline-blue-600'
                    : 'bg-blue-600 text-white shadow-sm hover:bg-blue-500 focus-visible:outline-blue-600'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {loading === plan.id ? 'Processing...' : `Get started with ${plan.name}`}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* FAQ section */}
      <div className="bg-gray-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-4xl divide-y divide-gray-900/10">
            <h2 className="text-2xl font-bold leading-10 tracking-tight text-gray-900">
              Frequently asked questions
            </h2>
            <dl className="mt-10 space-y-8 divide-y divide-gray-900/10">
              <div className="pt-8 lg:grid lg:grid-cols-12 lg:gap-8">
                <dt className="text-base font-semibold leading-7 text-gray-900 lg:col-span-5">
                  What&apos;s included in the free trial?
                </dt>
                <dd className="mt-4 lg:col-span-7 lg:mt-0">
                  <p className="text-base leading-7 text-gray-600">
                    The free trial includes access to all features for 14 days. You can create filters, 
                    receive alerts, and explore the platform without any limitations.
                  </p>
                </dd>
              </div>
              <div className="pt-8 lg:grid lg:grid-cols-12 lg:gap-8">
                <dt className="text-base font-semibold leading-7 text-gray-900 lg:col-span-5">
                  Can I change plans anytime?
                </dt>
                <dd className="mt-4 lg:col-span-7 lg:mt-0">
                  <p className="text-base leading-7 text-gray-600">
                    Yes, you can upgrade or downgrade your plan at any time. Changes take effect 
                    immediately, and we&apos;ll prorate any billing differences.
                  </p>
                </dd>
              </div>
              <div className="pt-8 lg:grid lg:grid-cols-12 lg:gap-8">
                <dt className="text-base font-semibold leading-7 text-gray-900 lg:col-span-5">
                  What payment methods do you accept?
                </dt>
                <dd className="mt-4 lg:col-span-7 lg:mt-0">
                  <p className="text-base leading-7 text-gray-600">
                    We accept all major credit cards (Visa, MasterCard, American Express) and 
                    process payments securely through Stripe.
                  </p>
                </dd>
              </div>
              <div className="pt-8 lg:grid lg:grid-cols-12 lg:gap-8">
                <dt className="text-base font-semibold leading-7 text-gray-900 lg:col-span-5">
                  How accurate are the tender alerts?
                </dt>
                <dd className="mt-4 lg:col-span-7 lg:mt-0">
                  <p className="text-base leading-7 text-gray-600">
                    Our AI-powered filtering system achieves 95%+ accuracy in matching tenders 
                    to your criteria. We continuously improve our algorithms based on user feedback.
                  </p>
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      {/* CTA section */}
      <div className="bg-blue-600">
        <div className="px-6 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to get started?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-blue-100">
              Join hundreds of companies already saving time and winning more contracts with our platform.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              {hasClerkKeys ? (
                <SignUpButton mode="modal">
                  <button className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-blue-600 shadow-sm hover:bg-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
                    Start free trial
                  </button>
                </SignUpButton>
              ) : (
                <Link href="/" className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-blue-600 shadow-sm hover:bg-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
                  Start free trial
                </Link>
              )}
              <Link href="/" className="text-sm font-semibold leading-6 text-white hover:text-blue-100">
                Learn more <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
