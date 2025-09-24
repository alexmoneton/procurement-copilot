import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy - TenderPulse',
  description: 'Privacy Policy for TenderPulse - GDPR compliant data protection for European public contracts',
}

export default function PrivacyPage() {
  return (
    <div className="bg-white py-24 sm:py-32">
      <div className="mx-auto max-w-4xl px-6 lg:px-8">
        <div className="mx-auto max-w-2xl lg:max-w-none">
          <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-6xl" style={{fontFamily: 'Manrope, sans-serif'}}>
            Privacy Policy
          </h1>
          <p className="mt-6 text-lg leading-8 text-gray-600">
            Last updated: September 24, 2025
          </p>
        </div>

        <div className="mt-16 prose prose-lg max-w-none">
          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            GDPR Compliance Statement
          </h2>
          <p className="text-gray-600 mb-6">
            TenderPulse is fully compliant with the General Data Protection Regulation (GDPR) and is committed to protecting your privacy and personal data. This policy explains how we collect, use, and protect your information.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            1. Data Controller
          </h2>
          <p className="text-gray-600 mb-6">
            TenderPulse acts as the data controller for the personal data we process. Our contact information:
            <br />
            Email: privacy@tenderpulse.eu
            <br />
            Address: TenderPulse, EU Region
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            2. Personal Data We Collect
          </h2>
          <div className="text-gray-600 mb-6">
            <p className="mb-4">We collect the following types of personal data:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Account Information:</strong> Email address, name, company information</li>
              <li><strong>Usage Data:</strong> Login times, feature usage, alert preferences</li>
              <li><strong>Payment Information:</strong> Billing details (processed securely by Stripe)</li>
              <li><strong>Communication Data:</strong> Support tickets, feedback, and correspondence</li>
            </ul>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            3. Legal Basis for Processing
          </h2>
          <div className="text-gray-600 mb-6">
            <p className="mb-4">We process your personal data based on:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Contract Performance:</strong> To provide our service as agreed</li>
              <li><strong>Legitimate Interest:</strong> To improve our service and prevent fraud</li>
              <li><strong>Consent:</strong> For marketing communications (where applicable)</li>
              <li><strong>Legal Obligation:</strong> For tax and accounting purposes</li>
            </ul>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            4. How We Use Your Data
          </h2>
          <div className="text-gray-600 mb-6">
            <p className="mb-4">We use your personal data to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Provide and maintain our service</li>
              <li>Process payments and manage subscriptions</li>
              <li>Send you tender alerts and notifications</li>
              <li>Provide customer support</li>
              <li>Improve our service and develop new features</li>
              <li>Comply with legal obligations</li>
            </ul>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            5. Data Sharing and Transfers
          </h2>
          <p className="text-gray-600 mb-6">
            We do not sell your personal data. We may share data with:
            <br />
            • <strong>Service Providers:</strong> Stripe (payments), SendGrid (emails), Railway (hosting)
            <br />
            • <strong>Legal Requirements:</strong> When required by law or to protect our rights
            <br />
            • <strong>Business Transfers:</strong> In case of merger or acquisition
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            6. Your Rights Under GDPR
          </h2>
          <div className="text-gray-600 mb-6">
            <p className="mb-4">You have the following rights:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Right of Access:</strong> Request copies of your personal data</li>
              <li><strong>Right to Rectification:</strong> Correct inaccurate or incomplete data</li>
              <li><strong>Right to Erasure:</strong> Request deletion of your personal data</li>
              <li><strong>Right to Restrict Processing:</strong> Limit how we use your data</li>
              <li><strong>Right to Data Portability:</strong> Receive your data in a structured format</li>
              <li><strong>Right to Object:</strong> Object to processing based on legitimate interests</li>
              <li><strong>Right to Withdraw Consent:</strong> Withdraw consent at any time</li>
            </ul>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            7. Data Security
          </h2>
          <p className="text-gray-600 mb-6">
            We implement appropriate technical and organizational measures to protect your personal data against unauthorized access, alteration, disclosure, or destruction. This includes encryption, secure servers, and regular security assessments.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            8. Data Retention
          </h2>
          <p className="text-gray-600 mb-6">
            We retain your personal data only as long as necessary for the purposes outlined in this policy, or as required by law. Account data is typically retained for the duration of your subscription plus 3 years for legal and accounting purposes.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            9. Cookies and Tracking
          </h2>
          <p className="text-gray-600 mb-6">
            We use essential cookies for authentication and service functionality. We do not use tracking cookies or third-party analytics without your explicit consent.
          </p>

          <h2 className="text-2xl font-bold text-gray-900 mb-4" style={{fontFamily: 'Manrope, sans-serif'}}>
            10. Contact Us
          </h2>
          <p className="text-gray-600 mb-6">
            To exercise your rights or for any privacy-related questions, contact us at:
            <br />
            Email: privacy@tenderpulse.eu
            <br />
            <br />
            You also have the right to lodge a complaint with your local data protection authority if you believe we have not handled your personal data in accordance with GDPR.
          </p>
        </div>
      </div>
    </div>
  )
}
