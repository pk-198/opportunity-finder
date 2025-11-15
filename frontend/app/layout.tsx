/**
 * Root layout component for Next.js app.
 * Wraps all pages with HTML structure and global styles.
 */

import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Email Analysis Tool',
  description: 'Analyze Gmail emails with AI-powered insights',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  )
}
