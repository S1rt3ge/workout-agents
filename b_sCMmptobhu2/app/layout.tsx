import type { Metadata } from 'next'
import { Inter, Space_Grotesk } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
})

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-space-grotesk',
})

export const metadata: Metadata = {
  title: 'WorkoutAgent — AI-Powered Training That Knows You',
  description: '8 AI agents. Zero generic plans. Total safety. WorkoutAgent builds personalized workout plans powered by a multi-agent system.',
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${inter.variable} ${spaceGrotesk.variable} bg-background`}>
      <body suppressHydrationWarning className="font-sans antialiased grain-overlay">
        {children}
        {process.env.NODE_ENV === 'production' && <Analytics />}
      </body>
    </html>
  )
}
