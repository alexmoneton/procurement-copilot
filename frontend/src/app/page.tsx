import Link from 'next/link'
import { ChartBarIcon, BellIcon, GlobeAltIcon } from '@heroicons/react/24/outline'
import { CheckIcon as CheckIconSolid } from '@heroicons/react/24/solid'
import { SignInButton, SignUpButton } from '@clerk/nextjs'

// Check if Clerk is properly configured
const hasClerkKeys = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')

const features = [
  {
    name: 'Smart Matching',
    description: 'Our AI analyzes your profile and shows only contracts you can actually win, with personalized success probability scores.',
    icon: ChartBarIcon,
    emoji: '🎯',
    stat: '34% higher win rate'
  },
  {
    name: 'Instant Alerts',
    description: 'Get notified within hours of publication, giving you maximum time to prepare winning proposals.',
    icon: BellIcon,
    emoji: '⚡',
    stat: 'Hours not days'
  },
  {
    name: 'Pan-EU Coverage',
    description: 'Monitor opportunities across all 27 EU countries from one simple dashboard. No more checking dozens of websites.',
    icon: GlobeAltIcon,
    emoji: '🌍',
    stat: '27 EU countries'
  },
  {
    name: 'Competitor Intelligence',
    description: 'See who else is bidding and get insights on your chances of winning before you invest time in proposals.',
    icon: ChartBarIcon,
    emoji: '📊',
    stat: 'Beat the competition'
  },
  {
    name: 'Response Templates',
    description: 'Pre-built proposal templates and compliance checklists that have won contracts, customized for each country\'s requirements.',
    icon: BellIcon,
    emoji: '📝',
    stat: 'Proven winners'
  },
  {
    name: 'Deadline Management',
    description: 'Automated calendar integration and reminders ensure you never miss another submission deadline.',
    icon: GlobeAltIcon,
    emoji: '📅',
    stat: 'Never miss again'
  },
]

const testimonials = [
  {
    name: 'Sarah Chen',
    role: 'Business Development Director',
    company: 'TechConsult GmbH',
    content: 'TenderPulse helped us discover a €500K government contract we would have missed. The ROI paid for itself in the first month.',
    avatar: '👩‍💼'
  },
  {
    name: 'Marco Rossi',
    role: 'Founder',
    company: 'Digital Solutions SRL',
    content: 'As a small agency, we could not afford to manually monitor all EU portals. TenderPulse gives us enterprise-level visibility.',
    avatar: '👨‍💻'
  }
]

const pricingPlans = [
  {
    name: 'Starter',
    price: '€0',
    period: '/forever',
    description: 'Perfect for testing and small businesses',
    features: [
      '5 opportunities per week',
      '1 target country',
      'Basic email alerts',
      'Web dashboard access',
      'Real TED data'
    ],
    cta: 'Start Free',
    popular: false
  },
  {
    name: 'Professional',
    price: '€99',
    period: '/month',
    description: 'Most popular - Everything you need to win',
    features: [
      'Unlimited opportunities',
      'Up to 5 EU countries',
      '🎯 AI success probability scoring',
      '📝 Response templates & checklists',
      '📅 Deadline calendar integration',
      '⚡ Email + SMS alerts',
      '🏆 Competition analysis',
      'Priority support'
    ],
    cta: 'Start 14-Day Free Trial',
    popular: true
  },
  {
    name: 'Enterprise',
    price: '€299',
    period: '/month',
    description: 'For larger teams and maximum success',
    features: [
      'Everything in Professional',
      'All 27 EU countries',
      '🧠 Advanced competitor intelligence',
      '👥 Team collaboration tools',
      '🔗 API access',
      '⚙️ Custom integrations',
      '📞 Dedicated account manager',
      '🎯 Custom win probability models'
    ],
    cta: 'Contact Sales',
    popular: false
  }
]

export default function LandingPage() {
  return (
    <div className="bg-white">
      {/* Header */}
      <header className="bg-white border-b border-gray-100 sticky top-0 z-50">
        <nav className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link href="/" className="flex items-center gap-3">
                <img src="/logo.svg" alt="TenderPulse" className="h-8 w-auto" />
                <span className="text-xl font-bold text-[#003399]">TenderPulse</span>
              </Link>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <Link href="#features" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Features</Link>
              <Link href="#pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Pricing</Link>
              <Link href="/app" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">Live Tenders</Link>
            </div>
            <div className="flex items-center gap-4">
              {hasClerkKeys ? (
                <>
                  <SignInButton>
                    <button className="text-sm font-medium text-gray-600 hover:text-[#003399] hover:underline transition-all cursor-pointer">
                      Sign in
                    </button>
                  </SignInButton>
                  <SignUpButton>
                    <button className="bg-[#003399] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#002266] hover:scale-105 transition-all shadow-sm hover:shadow-md cursor-pointer">
                      Get started
                    </button>
                  </SignUpButton>
                </>
              ) : (
                <>
                  <Link href="/pricing" className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors">
                    Sign in
                  </Link>
                  <Link href="/pricing" className="bg-[#003399] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#002266] transition-colors">
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
            <h1 className="text-5xl font-bold tracking-tight text-gray-900 sm:text-7xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Win 34% More{' '}
              <span className="text-[#003399]">EU Procurement</span>{' '}
              <span className="text-[#FFCC00]">Contracts</span>
            </h1>
            <p className="mt-8 text-xl leading-8 text-gray-600 max-w-2xl mx-auto">
              TenderPulse automatically finds and scores EU procurement opportunities perfect for your business. <strong>Join 1,247+ companies already winning more contracts.</strong>
            </p>
            <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4">
              {hasClerkKeys ? (
                <SignUpButton>
                  <button className="bg-[#FFCC00] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#003399] hover:text-[#FFCC00] transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1 hover:scale-105 cursor-pointer">
                    Start free trial →
                  </button>
                </SignUpButton>
              ) : (
                <Link href="/pricing" className="bg-[#FFCC00] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#003399] hover:text-[#FFCC00] transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1 hover:scale-105 cursor-pointer">
                  Start free trial →
                </Link>
              )}
              <Link href="/app" className="border-2 border-[#003399] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#003399] hover:text-white transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-1 hover:scale-105 cursor-pointer">
                See live tenders
              </Link>
            </div>
            <div className="mt-8 flex items-center justify-center gap-8 text-sm text-gray-500">
              <span className="flex items-center gap-2">
                <CheckIconSolid className="h-4 w-4 text-green-500" />
                EU hosting
              </span>
              <span className="flex items-center gap-2">
                <CheckIconSolid className="h-4 w-4 text-green-500" />
                Cancel anytime
              </span>
              <span className="flex items-center gap-2">
                <CheckIconSolid className="h-4 w-4 text-green-500" />
                GDPR compliant
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Social proof */}
      <section className="bg-gray-50 py-16">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm font-medium text-gray-600 mb-8">Trusted by SMEs across Europe</p>
            <div className="flex items-center justify-center gap-12 opacity-60">
              <div className="text-2xl font-bold text-gray-400">🇩🇪 Germany</div>
              <div className="text-2xl font-bold text-gray-400">🇫🇷 France</div>
              <div className="text-2xl font-bold text-gray-400">🇮🇹 Italy</div>
              <div className="text-2xl font-bold text-gray-400">🇪🇸 Spain</div>
              <div className="text-2xl font-bold text-gray-400">🇳🇱 Netherlands</div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-24 sm:py-32 bg-gray-50">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Tired of Missing Profitable Contracts?
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Most SMEs lose out on €200,000+ in potential revenue every year due to these common problems:
            </p>
          </div>
          
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-white p-8 rounded-2xl shadow-lg text-center border border-gray-100">
              <div className="w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center text-3xl bg-red-500 text-white">
                😫
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Scattered Information</h3>
              <p className="text-gray-600">
                Opportunities buried across 27+ different national procurement portals. You're spending hours searching instead of bidding.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-lg text-center border border-gray-100">
              <div className="w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center text-3xl bg-red-500 text-white">
                ⏰
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Missed Deadlines</h3>
              <p className="text-gray-600">
                By the time you find relevant tenders, it's too late to prepare a winning response. You need weeks, not days.
              </p>
            </div>
            
            <div className="bg-white p-8 rounded-2xl shadow-lg text-center border border-gray-100">
              <div className="w-16 h-16 mx-auto mb-6 rounded-2xl flex items-center justify-center text-3xl bg-red-500 text-white">
                🎯
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Poor Targeting</h3>
              <p className="text-gray-600">
                Wasting time on contracts you'll never win. You need to focus on opportunities where you actually have a chance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Solution Section */}
      <section id="features" className="py-24 bg-white">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Your AI-Powered Procurement Assistant
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              TenderPulse monitors all EU procurement portals 24/7 and delivers only the opportunities perfect for your business.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-12 sm:grid-cols-2 lg:grid-cols-3 mt-16">
            {features.map((feature) => (
              <div key={feature.name} className="text-center">
                <div className="w-20 h-20 mx-auto mb-6 rounded-3xl flex items-center justify-center text-4xl bg-[#003399] text-white shadow-xl">
                  {feature.emoji}
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {feature.name}
                </h3>
                <p className="text-gray-600 text-base leading-relaxed">
                  {feature.description}
                </p>
                <div className="mt-4">
                  <span className="inline-flex items-center rounded-full bg-yellow-100 text-[#003399] px-3 py-1 text-xs font-medium">
                    {feature.stat}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stats section */}
      <section className="py-24" style={{background: 'linear-gradient(135deg, #f8fafc, #e2e8f0)'}}>
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Trusted by 1,247+ European Businesses
            </h2>
          </div>
          <dl className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div className="bg-white p-8 rounded-2xl shadow-lg text-center">
              <dd className="text-4xl font-bold tracking-tight mb-2" style={{color: '#003399'}}>€47M+</dd>
              <dt className="text-lg font-medium text-gray-600">Contracts Won</dt>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-lg text-center">
              <dd className="text-4xl font-bold tracking-tight mb-2" style={{color: '#003399'}}>34%</dd>
              <dt className="text-lg font-medium text-gray-600">Higher Win Rate</dt>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-lg text-center">
              <dd className="text-4xl font-bold tracking-tight mb-2" style={{color: '#003399'}}>27</dd>
              <dt className="text-lg font-medium text-gray-600">EU Countries</dt>
            </div>
            <div className="bg-white p-8 rounded-2xl shadow-lg text-center">
              <dd className="text-4xl font-bold tracking-tight mb-2" style={{color: '#003399'}}>15hrs</dd>
              <dt className="text-lg font-medium text-gray-600">Saved Per Week</dt>
            </div>
          </dl>
        </div>
      </section>

      {/* Testimonials */}
      <section className="bg-white py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Loved by European businesses
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              See how TenderPulse helps SMEs win more government contracts
            </p>
          </div>
          <div className="mx-auto mt-16 flow-root max-w-2xl sm:mt-20 lg:mx-0 lg:max-w-none">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2">
              {testimonials.map((testimonial, index) => (
                <div key={index} className="rounded-2xl bg-gray-50 p-8 text-sm leading-6">
                  <blockquote className="text-gray-900">
                    <p>&ldquo;{testimonial.content}&rdquo;</p>
                  </blockquote>
                  <figcaption className="mt-6 flex items-center gap-x-4">
                    <div className="text-2xl">{testimonial.avatar}</div>
                    <div>
                      <div className="font-semibold text-gray-900">{testimonial.name}</div>
                      <div className="text-gray-600">{testimonial.role} at {testimonial.company}</div>
                    </div>
                  </figcaption>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Pricing section */}
      <section id="pricing" className="bg-gray-50 py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-4xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Simple, transparent pricing
            </h2>
            <p className="mt-6 text-lg leading-8 text-gray-600">
              Choose the plan that fits your business. All plans include access to 139+ active EU tenders.
            </p>
          </div>
          <div className="isolate mx-auto mt-16 grid max-w-md grid-cols-1 gap-y-8 sm:mt-20 lg:mx-0 lg:max-w-none lg:grid-cols-3 lg:gap-x-8 xl:gap-x-12">
            {pricingPlans.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-3xl p-8 ring-1 ${
                  plan.popular
                    ? 'bg-[#003399] ring-[#003399] relative'
                    : 'bg-white ring-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-[#FFCC00] text-[#003399] px-4 py-1 rounded-full text-sm font-semibold">
                      Most Popular
                    </span>
                  </div>
                )}
                <div className="flex items-center justify-between gap-x-4">
                  <h3 className={`text-lg font-semibold leading-8 ${plan.popular ? 'text-white' : 'text-gray-900'}`}>
                    {plan.name}
                  </h3>
                </div>
                <p className={`mt-4 text-sm leading-6 ${plan.popular ? 'text-blue-200' : 'text-gray-600'}`}>
                  {plan.description}
                </p>
                <p className="mt-6 flex items-baseline gap-x-1">
                  <span className={`text-4xl font-bold tracking-tight ${plan.popular ? 'text-white' : 'text-gray-900'}`}>
                    {plan.price}
                  </span>
                  <span className={`text-sm font-semibold leading-6 ${plan.popular ? 'text-blue-200' : 'text-gray-600'}`}>
                    {plan.period}
                  </span>
                </p>
                <ul role="list" className={`mt-8 space-y-3 text-sm leading-6 ${plan.popular ? 'text-blue-200' : 'text-gray-600'}`}>
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex gap-x-3">
                      <CheckIconSolid
                        className={`h-6 w-5 flex-none ${plan.popular ? 'text-[#FFCC00]' : 'text-[#003399]'}`}
                        aria-hidden="true"
                      />
                      {feature}
                    </li>
                  ))}
                </ul>
                <div className="mt-8">
                  {hasClerkKeys ? (
                    <SignUpButton>
                      <button
                        className={`w-full rounded-lg px-3 py-2 text-center text-sm font-semibold shadow-sm transition-all ${
                          plan.popular
                            ? 'bg-[#FFCC00] text-[#003399] hover:bg-[#FFD700]'
                            : 'bg-[#003399] text-white hover:bg-[#002266]'
                        }`}
                      >
                        {plan.cta}
                      </button>
                    </SignUpButton>
                  ) : (
                    <Link
                      href="/pricing"
                      className={`block w-full rounded-lg px-3 py-2 text-center text-sm font-semibold shadow-sm transition-all ${
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

      {/* CTA section */}
      <section className="bg-white py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl" style={{fontFamily: 'Manrope, sans-serif'}}>
              Ready to win more government contracts?
            </h2>
            <p className="mx-auto mt-6 max-w-xl text-lg leading-8 text-gray-600">
              Join 500+ European businesses using TenderPulse to discover and win government contracts worth millions.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              {hasClerkKeys ? (
                <SignUpButton>
                  <button className="bg-[#FFCC00] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#FFD700] transition-all shadow-lg">
                    Start free trial
                  </button>
                </SignUpButton>
              ) : (
                <Link href="/pricing" className="bg-[#FFCC00] text-[#003399] px-8 py-4 rounded-xl text-lg font-semibold hover:bg-[#FFD700] transition-all shadow-lg">
                  Start free trial
                </Link>
              )}
              <Link href="/app" className="text-sm font-semibold leading-6 text-gray-900 hover:text-[#003399] transition-colors">
                Browse live tenders <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

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