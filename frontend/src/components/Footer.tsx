import Link from 'next/link'
import Image from 'next/image'

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="mx-auto max-w-7xl px-6 py-12 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <Image src="/logo.svg" alt="TenderPulse" width={32} height={32} className="h-8 w-8" />
              <span className="text-xl font-bold text-[#003399]" style={{fontFamily: 'Manrope, sans-serif'}}>
                TenderPulse
              </span>
            </div>
            <p className="text-gray-600 text-sm max-w-md">
              Real-time signals for European public contracts. Monitor 200+ active tenders worth €800M+ across 10 EU countries.
            </p>
          </div>

          {/* Product */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              Product
            </h3>
            <ul className="space-y-3">
              <li>
                <Link href="/app" className="text-sm text-gray-600 hover:text-[#003399] transition-colors">
                  Dashboard
                </Link>
              </li>
              <li>
                <Link href="/pricing" className="text-sm text-gray-600 hover:text-[#003399] transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="/features" className="text-sm text-gray-600 hover:text-[#003399] transition-colors">
                  Features
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
              Legal
            </h3>
            <ul className="space-y-3">
              <li>
                <Link href="/terms" className="text-sm text-gray-600 hover:text-[#003399] transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/privacy" className="text-sm text-gray-600 hover:text-[#003399] transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-sm text-gray-600 hover:text-[#003399] transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-500">
              © 2025 TenderPulse. All rights reserved.
            </p>
            <p className="text-sm text-gray-500 mt-2 md:mt-0">
              🇪🇺 EU-based • GDPR Compliant • Independent
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}
