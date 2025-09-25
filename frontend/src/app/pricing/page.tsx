'use client'

import Link from 'next/link'
import Image from 'next/image'
import { CheckIcon } from '@heroicons/react/24/solid'
import { SignInButton, SignUpButton } from '@clerk/nextjs'
import { useState } from 'react'

// Check if Clerk is properly configured
const hasClerkKeys = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

// Get Stripe price IDs from environment variables
const getStripePriceIds = () => {
  try {
    const priceIdsJson = process.env.NEXT_PUBLIC_STRIPE_PRICE_IDS
    if (priceIdsJson) {
      return JSON.parse(priceIdsJson)
    }
  } catch (error) {
    console.error('Error parsing Stripe price IDs:', error)
  }
  // Fallback to placeholder IDs if not configured
  return {
    starter: 'price_starter',
    pro: 'price_pro', 
    team: 'price_team'
  }
}

const stripePriceIds = getStripePriceIds()

const pricingPlans = [
  {
    name: 'Starter',
    price: '€99',
    period: '/month',
    description: 'Perfect for solo consultants and small agencies',
    features: [
      '1 saved filter',
      'Daily email alerts',
      'Access to all EU tenders',
      'Basic support',
      'Email notifications',
      'Tender export (CSV)'
    ],
    cta: 'Start 14-day free trial',
    popular: false,
    priceId: stripePriceIds.starter
  },
  {
    name: 'Pro',
    price: '€199',
    period: '/month',
    description: 'Ideal for growing businesses and BD teams',
    features: [
      '5 saved filters',
      'Daily + weekly alerts',
      'Priority support',
      'Advanced analytics',
      'Export capabilities',
      'Team collaboration',
      'Custom CPV filtering',
      'Value range alerts'
    ],
    cta: 'Start 14-day free trial',
    popular: true,
    priceId: stripePriceIds.pro
  },
  {
    name: 'Team',
    price: '€399',
    period: '/month',
    description: 'For larger companies and procurement departments',
    features: [
      '15 saved filters',
      'Team management',
      'Custom integrations',
      'Dedicated support',
      'API access',
      'White-label options',
      'Custom reporting',
      'SLA guarantee',
      'Phone support'
    ],
    cta: 'Contact sales',
    popular: false,
    priceId: stripePriceIds.team
  }
]

const faqs = [
  {
    question: 'How quickly do I get alerts?',
    answer: 'TenderPulse monitors procurement portals every 6 hours and sends alerts within minutes of new tender publication. You\'ll typically receive alerts the same day tenders are published.'
  },
  {
    question: 'Which countries are covered?',
    answer: 'We monitor TED (all EU countries) plus national portals in Germany, France, Italy, Spain, Netherlands, and the UK. Coverage includes 139+ active tenders worth over €800M.'
  },
  {
    question: 'Can I cancel anytime?',
    answer: 'Yes, absolutely. You can cancel your subscription at any time from your account settings. No long-term contracts or cancellation fees.'
  },
  {
    question: 'Do you offer refunds?',
    answer: 'We offer a 14-day money-back guarantee. If you\'re not satisfied with TenderPulse, contact us within 14 days for a full refund.'
  }
]

export default function PricingPage() {
  const [loading, setLoading] = useState<string | null>(null)

  const handleCheckout = async (priceId: string) => {
    setLoading(priceId)
    try {
      const response = await fetch('/api/stripe/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ price_id: priceId }),
      })

      const data = await response.json()
      
      if (data.url) {
        window.location.href = data.url
      } else {
        console.error('No checkout URL returned')
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
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <nav className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="flex items-center gap-3">
                <Image src="/logo.svg" alt="TenderPulse" width={32} height={32} className="h-8 w-auto" />
                <span className="text-xl font-bold text-[#003399]">TenderPulse</span>
              </Link>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <Link href="/#features" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Features</Link>
              <Link href="/pricing" className="text-sm font-medium text-[#003399] font-semibold">Pricing</Link>
              <Link href="/app" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Live Tenders</Link>
            </div>
            <div className="flex items-center gap-4">
              {hasClerkKeys ? (
                <>
                  <SignInButton mode="modal">
                    <button className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                      Sign in
                    </button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button className="bg-[#003399] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#002266] transition-colors">
                      Get started
                    </button>
                  </SignUpButton>
                </>
              ) : (
                <>
                  <Link href="/app" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                    Sign in
                  </Link>
                  <Link href="/app" className="bg-[#003399] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#002266] transition-colors">
                    Get started
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>
      </header>

      {/* Hero section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-white to-gray-50 py-20 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-3xl text-center">
            <div className="mb-8">
              <span className="inline-flex items-center gap-2 rounded-full bg-[#003399]/10 px-4 py-2 text-sm font-medium text-[#003399]">
                <span className="h-2 w-2 rounded-full bg-[#FFCC00] animate-pulse"></span>
                139+ active EU tenders worth €800M+
              </span>
            </div>
            <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-6xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Simple, transparent{' '}
              <span className="text-[#003399]">pricing</span>
            </h1>
            <p className="mt-8 text-xl leading-8 text-gray-600 max-w-2xl mx-auto">
              Choose the plan that fits your business. All plans include access to 139+ active EU tenders. Start with a free trial.
            </p>
          </div>
        </div>
      </section>

      {/* Pricing section */}
      <section className="bg-white py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="isolate mx-auto grid max-w-md grid-cols-1 gap-y-8 sm:mt-20 lg:mx-0 lg:max-w-none lg:grid-cols-3 lg:gap-x-8 xl:gap-x-12">
            {pricingPlans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-3xl p-8 ring-1 ${
                  plan.popular
                    ? 'bg-[#003399] ring-[#003399] relative scale-105'
                    : 'bg-white ring-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-[#FFCC00] text-[#003399] px-4 py-2 rounded-full text-sm font-semibold shadow-lg">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="flex items-center justify-between gap-x-4">
                  <h3 className={`text-xl font-semibold leading-8 ${plan.popular ? 'text-white' : 'text-gray-900'}`} style={{fontFamily: 'Manrope, sans-serif'}}>
                    {plan.name}
                  </h3>
                </div>
                <p className={`mt-4 text-sm leading-6 ${plan.popular ? 'text-blue-200' : 'text-gray-600'}`}>
                  {plan.description}
                </p>
                <p className="mt-6 flex items-baseline gap-x-1">
                  <span className={`text-5xl font-bold tracking-tight ${plan.popular ? 'text-white' : 'text-gray-900'}`} style={{fontFamily: 'Manrope, sans-serif'}}>
                    {plan.price}
                  </span>
                  <span className={`text-lg font-semibold leading-6 ${plan.popular ? 'text-blue-200' : 'text-gray-600'}`}>
                    {plan.period}
                  </span>
                </p>
                <ul role="list" className={`mt-8 space-y-3 text-sm leading-6 ${plan.popular ? 'text-blue-200' : 'text-gray-600'}`}>
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex gap-x-3">
                      <CheckIcon
                        className={`h-6 w-5 flex-none ${plan.popular ? 'text-[#FFCC00]' : 'text-[#003399]'}`}
                        aria-hidden="true"
                      />
                      {feature}
                    </li>
                  ))}
                </ul>
                <div className="mt-10">
                  {hasClerkKeys ? (
                    <button
                      onClick={() => handleCheckout(plan.priceId)}
                      disabled={loading === plan.priceId}
                      className={`w-full rounded-xl px-6 py-4 text-center text-lg font-semibold shadow-lg transition-all hover:shadow-xl transform hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed ${
                        plan.popular
                          ? 'bg-[#FFCC00] text-[#003399] hover:bg-[#FFD700]'
                          : 'bg-[#003399] text-white hover:bg-[#002266]'
                      }`}
                    >
                      {loading === plan.priceId ? 'Processing...' : plan.cta}
                    </button>
                  ) : (
                    <Link
                      href="/app"
                      className={`block w-full rounded-xl px-6 py-4 text-center text-lg font-semibold shadow-lg transition-all hover:shadow-xl transform hover:-translate-y-0.5 ${
                        plan.popular
                          ? 'bg-[#FFCC00] text-[#003399] hover:bg-[#FFD700]'
                          : 'bg-[#003399] text-white hover:bg-[#002266]'
                      }`}
                    >
                      {plan.cta}
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats section */}
      <section className="bg-[#003399] py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:max-w-none">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
                What you get with every plan
              </h2>
              <p className="mt-4 text-lg leading-8 text-blue-200">
                Access to live European procurement data, updated daily
              </p>
            </div>
            <dl className="mt-16 grid grid-cols-1 gap-0.5 overflow-hidden rounded-2xl text-center sm:grid-cols-2 lg:grid-cols-4">
              <div className="flex flex-col bg-white/5 p-8">
                <dt className="text-sm font-semibold leading-6 text-blue-200">Active Tenders</dt>
                <dd className="order-first text-3xl font-bold tracking-tight text-white">139+</dd>
              </div>
              <div className="flex flex-col bg-white/5 p-8">
                <dt className="text-sm font-semibold leading-6 text-blue-200">Total Value</dt>
                <dd className="order-first text-3xl font-bold tracking-tight text-white">€800M+</dd>
              </div>
              <div className="flex flex-col bg-white/5 p-8">
                <dt className="text-sm font-semibold leading-6 text-blue-200">Countries</dt>
                <dd className="order-first text-3xl font-bold tracking-tight text-white">10+</dd>
              </div>
              <div className="flex flex-col bg-white/5 p-8">
                <dt className="text-sm font-semibold leading-6 text-blue-200">Avg. Value</dt>
                <dd className="order-first text-3xl font-bold tracking-tight text-white">€400K</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      {/* FAQ section */}
      <section className="bg-gray-50 py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-4xl">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
                Frequently asked questions
              </h2>
              <p className="mt-6 text-lg leading-8 text-gray-600">
                Everything you need to know about TenderPulse
              </p>
            </div>
            <div className="mt-16">
              <dl className="space-y-8">
                {faqs.map((faq) => (
                  <div key={faq.question} className="bg-white rounded-2xl p-8 shadow-sm">
                    <dt className="text-lg font-semibold leading-7 text-gray-900" style={{fontFamily: 'Manrope, sans-serif'}}>
                      {faq.question}
                    </dt>
                    <dd className="mt-2 text-base leading-7 text-gray-600">
                      {faq.answer}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          </div>
        </div>
      </section>

      {/* CTA section */}
      <section className="bg-white py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Ready to start winning more contracts?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-gray-600">
              Join 500+ European businesses using TenderPulse. Set up your first alert in under 5 minutes.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              {hasClerkKeys ? (
                <SignUpButton mode="modal">
                  <button className="bg-[#FFCC00] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#FFD700] transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
                    Start free trial →
                  </button>
                </SignUpButton>
              ) : (
                <Link href="/app" className="bg-[#FFCC00] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#FFD700] transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5">
                  Start free trial →
                </Link>
              )}
              <Link href="/app" className="border-2 border-[#003399] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#003399] hover:text-white transition-all">
                Browse live tenders
              </Link>
            </div>
            <div className="mt-8 flex items-center justify-center gap-8 text-sm text-gray-500">
              <span className="flex items-center gap-2">
                <CheckIcon className="h-4 w-4 text-green-500" />
                14-day money-back guarantee
              </span>
              <span className="flex items-center gap-2">
                <CheckIcon className="h-4 w-4 text-green-500" />
                Cancel anytime
              </span>
              <span className="flex items-center gap-2">
                <CheckIcon className="h-4 w-4 text-green-500" />
                EU hosting & GDPR compliant
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Image src="/logo.svg" alt="TenderPulse" width={32} height={32} className="h-8 w-auto" />
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