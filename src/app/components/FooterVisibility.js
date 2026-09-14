'use client'

import { usePathname } from 'next/navigation'
import Footer from './footer'

const HIDDEN_PATHS = new Set(['/', '/inscription', '/login', '/mdp-oublie'])

export default function FooterVisibility() {
  const pathname = usePathname()

  // Masquer le footer sur les pages de connexion/inscription et sur les pages GRC (qui ont leur propre layout)
  if (
    HIDDEN_PATHS.has(pathname) ||
    pathname?.startsWith('/admin') ||
    pathname?.startsWith('/vue') ||
    pathname?.startsWith('/analyses') ||
    pathname?.startsWith('/risques') ||
    pathname?.startsWith('/controles') ||
    pathname?.startsWith('/conformite') ||
    pathname?.startsWith('/rapports') ||
    pathname?.startsWith('/compte') ||
    pathname?.startsWith('/employe') ||
    pathname?.startsWith('/grc')
  ) {
    return null
  }

  return <Footer />
}

