import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service - TenderPulse',
  description: 'Terms of Service for TenderPulse - Real-time signals for European public contracts',
}

export default function TermsPage() {
  return (
    <div className="bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-4xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl lg:max-w-none">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl" style={{fontFamily: 'Manrope, sans-serif'}}>
            Terms of Service
          </h1>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Last updated: September 24, 2025
          </p>
        </div>

        <div className="mt-16 prose prose-lg max-w-none">
          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            1. Acceptance of Terms
          </h2>
          <p className="text-gray-600 mb-6">
            By accessing and using TenderPulse (&quot;the Service&quot;), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            2. Description of Service
          </h2>
          <p className="text-gray-600 mb-6">
            TenderPulse provides real-time monitoring and alerts for European public procurement opportunities. Our service aggregates data from official EU sources including TED (Tenders Electronic Daily) and national procurement platforms.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            3. User Accounts
          </h2>
          <p className="text-gray-600 mb-6">
            You are responsible for maintaining the confidentiality of your account and password. You agree to accept responsibility for all activities that occur under your account or password.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            4. Payment Terms
          </h2>
          <p className="text-gray-600 mb-6">
            Subscription fees are billed in advance on a monthly or annual basis. All fees are non-refundable except as required by law. We offer a 14-day free trial for new users.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            5. Data Usage
          </h2>
          <p className="text-gray-600 mb-6">
            Our service processes publicly available procurement data. We do not claim ownership of this data and provide it for informational purposes only. Users are responsible for verifying the accuracy and completeness of any information before making business decisions.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            6. Limitation of Liability
          </h2>
          <p className="text-gray-600 mb-6">
            TenderPulse shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            7. Termination
          </h2>
          <p className="text-gray-600 mb-6">
            We may terminate or suspend your account immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            8. Governing Law
          </h2>
          <p className="text-gray-600 mb-6">
            These Terms shall be interpreted and governed by the laws of the European Union, without regard to its conflict of law provisions.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            9. Contact Information
          </h2>
          <p className="text-gray-600 mb-6">
            If you have any questions about these Terms of Service, please contact us at:
            <br />
            Email: legal@tenderpulse.eu
            <br />
            Address: TenderPulse, EU Region
          </p>
        </div>
      </div>
    </div>
  )
}
