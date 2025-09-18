import Link from 'next/link'
import { ArrowRightIcon, CheckIcon, ChartBarIcon, BellIcon, GlobeAltIcon } from '@heroicons/react/24/outline'
import { SignInButton, SignUpButton } from '@clerk/nextjs'

// Check if Clerk is properly configured
const hasClerkKeys = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

const features = [
  {
    name: 'EU Portal Monitoring',
    description: 'Real-time monitoring of TED and national procurement portals across Europe. Clean, early signals delivered instantly.',
    icon: BellIcon,
  },
  {
    name: 'Smart Contract Matching',
    description: 'Advanced filters by sector, value, location, and keywords. Only get contracts that actually fit your business.',
    icon: ChartBarIcon,
  },
  {
    name: 'European Coverage',
    description: 'Monitor opportunities across all EU member states from a single platform. Never miss cross-border contracts.',
    icon: GlobeAltIcon,
  },
]

const benefits = [
  'Save 15+ hours per week on manual tender research',
  'Get alerts within hours of tender publication',
  'Access to 500,000+ annual European procurement opportunities',
  'Filter by CPV codes, value ranges, and geographic regions',
  'Direct email alerts with tender links and deadlines',
  'Never miss high-value contracts in your sector again',
]

export default function LandingPage() {
  return (
    <div className="bg-white">
      {/* Header */}
      <header className="absolute inset-x-0 top-0 z-50">
        <nav className="flex items-center justify-between p-6 lg:px-8" aria-label="Global">
          <div className="flex lg:flex-1">
            <Link href="/" className="-m-1.5 p-1.5 flex items-center gap-3">
              <img src="/logo.svg" alt="TenderPulse" className="h-10 w-auto" />
            </Link>
          </div>
          <div className="flex lg:flex-1 lg:justify-end">
            <div className="flex items-center gap-4">
              {hasClerkKeys ? (
                <>
                  <SignInButton mode="modal">
                    <button className="text-sm font-semibold leading-6 text-gray-900 hover:text-blue-600">
                      Sign in
                    </button>
                  </SignInButton>
                  <SignUpButton mode="modal">
                    <button className="rounded-md bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">
                      Get started
                    </button>
                  </SignUpButton>
                </>
              ) : (
                <>
                  <Link href="/pricing" className="text-sm font-semibold leading-6 text-gray-900 hover:text-blue-600">
                    Sign in
                  </Link>
                  <Link href="/pricing" className="rounded-md bg-blue-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600">
                    Get started
                  </Link>
                </>
              )}
            </div>
          </div>
        </nav>
      </header>

      {/* Hero section */}
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="absolute inset-x-0 -top-40 -z-10 transform-gpu overflow-hidden blur-3xl sm:-top-80" aria-hidden="true">
          <div
            className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]"
            style={{
              clipPath:
                'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
            }}
          />
        </div>
        <div className="mx-auto max-w-2xl py-32 sm:py-48 lg:py-56">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Never miss another tender.
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              EU & national portals monitored. Clean, early signals for contracts that fit you.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              {hasClerkKeys ? (
                <SignUpButton mode="modal">
                  <button className="btn-primary rounded-md px-6 py-3 text-sm font-semibold shadow-sm">
                    Start free trial
                    <ArrowRightIcon className="ml-2 h-4 w-4" />
                  </button>
                </SignUpButton>
              ) : (
                <Link href="/pricing" className="btn-primary rounded-md px-6 py-3 text-sm font-semibold shadow-sm inline-flex items-center">
                  Start free trial
                  <ArrowRightIcon className="ml-2 h-4 w-4" />
                </Link>
              )}
              <Link href="/app" className="btn-secondary rounded-md px-6 py-3 text-sm font-semibold inline-flex items-center">
                See live tenders <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
        <div
          className="absolute inset-x-0 top-[calc(100%-13rem)] -z-10 transform-gpu overflow-hidden blur-3xl sm:top-[calc(100%-30rem)]"
          aria-hidden="true"
        >
          <div
            className="relative left-[calc(50%+3rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30 sm:left-[calc(50%+36rem)] sm:w-[72.1875rem]"
            style={{
              clipPath:
                'polygon(74.1% 44.1%, 100% 61.6%, 97.5% 26.9%, 85.5% 0.1%, 80.7% 2%, 72.5% 32.5%, 60.2% 62.4%, 52.4% 68.1%, 47.5% 58.3%, 45.2% 34.5%, 27.5% 76.7%, 0.1% 64.9%, 17.9% 100%, 27.6% 76.8%, 76.1% 97.7%, 74.1% 44.1%)',
            }}
          />
        </div>
      </div>

      {/* Features section */}
      <div className="py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:text-center">
            <h2 className="text-base font-semibold leading-7 text-blue-600">Everything you need</h2>
            <p className="mt-2 text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              European procurement signals, simplified
            </p>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Monitor official EU procurement portals with intelligent filtering. Get early signals for contracts that match your business.
            </p>
          </div>
          <div className="mx-auto mt-16 max-w-2xl sm:mt-20 lg:mt-24 lg:max-w-none">
            <dl className="grid max-w-xl grid-cols-1 gap-x-8 gap-y-16 lg:max-w-none lg:grid-cols-3">
              {features.map((feature) => (
                <div key={feature.name} className="flex flex-col">
                  <dt className="flex items-center gap-x-3 text-base font-semibold leading-7 text-gray-900">
                    <feature.icon className="h-5 w-5 flex-none text-blue-600" aria-hidden="true" />
                    {feature.name}
                  </dt>
                  <dd className="mt-4 flex flex-auto flex-col text-base leading-7 text-gray-600">
                    <p className="flex-auto">{feature.description}</p>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* Benefits section */}
      <div className="bg-gray-50 py-24 sm:py-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:max-w-none">
            <div className="text-center">
              <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
                Why choose TenderPulse?
              </h2>
              <p className="mt-4 text-lg leading-8 text-gray-600">
                Join smart businesses already using TenderPulse to discover and win more European contracts.
              </p>
            </div>
            <dl className="mt-16 grid grid-cols-1 gap-8 sm:mt-20 sm:grid-cols-2 lg:grid-cols-3">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex flex-col-reverse">
                  <dt className="text-base leading-7 text-gray-900 flex items-center">
                    <CheckIcon className="h-5 w-5 text-green-500 mr-2 flex-shrink-0" />
                    {benefit}
                  </dt>
                </div>
              ))}
            </dl>
          </div>
        </div>
      </div>

      {/* CTA section */}
      <div className="bg-blue-600">
        <div className="px-6 py-24 sm:px-6 sm:py-32 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
              Ready to never miss another opportunity?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-blue-100">
              Start your free trial today and see how much time you can save with automated tender monitoring.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              {hasClerkKeys ? (
                <SignUpButton mode="modal">
                  <button className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-blue-600 shadow-sm hover:bg-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
                    Get started for free
                  </button>
                </SignUpButton>
              ) : (
                <Link href="/pricing" className="rounded-md bg-white px-3.5 py-2.5 text-sm font-semibold text-blue-600 shadow-sm hover:bg-blue-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white">
                  Get started for free
                </Link>
              )}
              <Link href="/pricing" className="text-sm font-semibold leading-6 text-white hover:text-blue-100">
                View pricing <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200">
        <div className="mx-auto max-w-7xl px-6 py-12 md:flex md:items-center md:justify-between lg:px-8">
          <div className="flex justify-center space-x-6 md:order-2">
            <Link href="/pricing" className="text-gray-400 hover:text-gray-500">
              Pricing
            </Link>
            <Link href="/app" className="text-gray-400 hover:text-gray-500">
              Live Tenders
            </Link>
            <Link href="/account" className="text-gray-400 hover:text-gray-500">
              Account
            </Link>
          </div>
          <div className="mt-8 md:order-1 md:mt-0">
            <p className="text-center text-xs leading-5 text-gray-500">
              &copy; 2025 TenderPulse. All rights reserved.
            </p>
            <p className="text-center text-xs leading-5 text-gray-400 mt-2">
              TenderPulse is an independent service and is not affiliated with the European Union or its institutions.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}