import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'TenderPulse — Real-time signals for public contracts',
  description: 'EU & national portals monitored. Clean, early signals for contracts that fit you. Never miss another tender opportunity.',
  keywords: ['tenders', 'public contracts', 'TED', 'EU procurement', 'alerts', 'monitoring', 'TenderPulse'],
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
        <body className={inter.className}>
          {children}
        </body>
      </html>
    )
  }
  
  return (
    <ClerkProvider>
      <html lang="en">
        <body className={inter.className}>
          {children}
        </body>
      </html>
    </ClerkProvider>
  )
}