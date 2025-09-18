import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TenderPulse — Real-time signals for public contracts',
  description: 'EU & national portals monitored. Clean, early signals for contracts that fit you. Never miss another tender opportunity.',
  keywords: ['tenders', 'public contracts', 'TED', 'EU procurement', 'alerts', 'monitoring', 'TenderPulse'],
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/icon.svg', type: 'image/svg+xml' }
    ],
    shortcut: '/favicon.svg',
    apple: '/icon.svg',
  },
  openGraph: {
    title: 'TenderPulse — Real-time signals for public contracts',
    description: 'Monitor 139+ active EU procurement opportunities worth €800M+. Never miss another government contract.',
    url: 'https://tenderpulse.eu',
    siteName: 'TenderPulse',
    images: [
      {
        url: '/logo.svg',
        width: 800,
        height: 600,
        alt: 'TenderPulse - EU Procurement Monitoring',
      },
    ],
    locale: 'en_EU',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'TenderPulse — Real-time signals for public contracts',
    description: 'Monitor 139+ active EU procurement opportunities worth €800M+',
    images: ['/logo.svg'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const hasClerkKeys = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.startsWith('pk_')
  
  if (!hasClerkKeys) {
    // Render without Clerk during build or when keys are missing
    return (
      <html lang="en">
        <head>
          <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
          <link rel="shortcut icon" href="/favicon.svg" />
          <link rel="apple-touch-icon" href="/icon.svg" />
        </head>
        <body className={inter.className}>
          {children}
        </body>
      </html>
    )
  }
  
  return (
    <ClerkProvider>
      <html lang="en">
        <head>
          <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
          <link rel="shortcut icon" href="/favicon.svg" />
          <link rel="apple-touch-icon" href="/icon.svg" />
        </head>
        <body className={inter.className}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}