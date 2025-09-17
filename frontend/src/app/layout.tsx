import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ClerkProvider } from '@clerk/nextjs'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Procurement Copilot - AI-Powered Tender Monitoring',
  description: 'Get automated alerts for public procurement opportunities matching your business needs. Monitor TED and BOAMP France tenders with AI-powered filtering.',
  keywords: ['procurement', 'tenders', 'public contracts', 'TED', 'BOAMP', 'alerts', 'monitoring'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
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