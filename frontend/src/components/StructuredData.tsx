export default function StructuredData() {
  const structuredData = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "TenderPulse",
    "description": "Real-time signals for European public contracts. Monitor 139+ active EU procurement opportunities worth €800M+.",
    "url": "https://tenderpulse.eu",
    "applicationCategory": "BusinessApplication",
    "operatingSystem": "Web",
    "offers": {
      "@type": "Offer",
      "price": "99",
      "priceCurrency": "EUR",
      "priceValidUntil": "2025-12-31"
    },
    "provider": {
      "@type": "Organization",
      "name": "TenderPulse",
      "url": "https://tenderpulse.eu",
      "logo": "https://tenderpulse.eu/logo.svg"
    },
    "featureList": [
      "Real-time EU tender monitoring",
      "AI-powered matching scores",
      "Email alerts",
      "Multi-country coverage",
      "CPV code filtering"
    ]
  }

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{
        __html: JSON.stringify(structuredData)
      }}
    />
  )
}
