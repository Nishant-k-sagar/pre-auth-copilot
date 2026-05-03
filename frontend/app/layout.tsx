import type { Metadata } from 'next'
import { DM_Sans } from 'next/font/google'
import './globals.css'
import { Navbar } from '@/components/layout/Navbar'

const dmSans = DM_Sans({ 
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-satoshi',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Pre-Auth Copilot',
  description: 'LLM-powered pre-authorization medical necessity reviewer',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth" suppressHydrationWarning>
      <body className={`${dmSans.className} min-h-screen bg-[var(--background)] text-[var(--foreground)]`}>
        <Navbar />
        <main className="responsive-container">
          {children}
        </main>
      </body>
    </html>
  )
}
