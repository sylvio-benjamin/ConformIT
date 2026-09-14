'use client'
import Link from 'next/link'
import React from 'react'

export default function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="mt-16 border-t border-slate-300 bg-slate-700 text-slate-100">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-10 px-6 py-12 lg:px-8">
        <div className="grid gap-10 text-left md:grid-cols-[1.5fr_1fr_1fr]">
          <div className="space-y-4">
            <div>
              <Link href="/vue" className="text-lg font-semibold text-white">
                ConformIT
              </Link>
              <p className="mt-2 text-sm text-slate-200">
                Analyse de documents, preuves, risques et conformité — un seul parcours.
              </p>
            </div>
            <div className="space-y-1 text-sm text-slate-200">
              <p>Siège social — 123 avenue de la République, 75011 Paris</p>
              <p>SIRET : 902 456 789 00017</p>
              <p>support@analysekbis.com • +33 (0)1 86 95 40 12</p>
            </div>
          </div>

          <nav className="grid gap-3 text-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-100/80">Ressources</p>
            <Link href="/conditions-utilisation" className="transition hover:text-white">
              Conditions d’utilisation
            </Link>
            <Link href="/politique-confidentialite" className="transition hover:text-white">
              Politique de confidentialité
            </Link>
            <Link href="/mentions-legales" className="transition hover:text-white">
              Mentions légales
            </Link>
            <Link href="/politique-confidentialite" className="transition hover:text-white">
              Protection des données (RGPD)
            </Link>
          </nav>

          <div className="grid gap-3 text-sm">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-100/80">Nous contacter</p>
            <Link href="mailto:commercial@analysekbis.com" className="transition hover:text-white">
              commercial@analysekbis.com
            </Link>
            <Link href="mailto:support@analysekbis.com" className="transition hover:text-white">
              support@analysekbis.com
            </Link>
            <Link href="tel:+33186954012" className="transition hover:text-white">
              +33 (0)1 86 95 40 12
            </Link>
            <div className="flex gap-4 pt-1 text-base text-slate-100">
              <Link href="https://www.linkedin.com" target="_blank" rel="noopener" className="hover:text-white">
                LinkedIn
              </Link>
              <Link href="https://twitter.com" target="_blank" rel="noopener" className="hover:text-white">
                X / Twitter
              </Link>
            </div>
          </div>
        </div>

        <div className="flex flex-col items-center gap-4 border-t border-slate-600 pt-6 text-center text-xs text-slate-200 md:flex-row md:justify-between md:text-left">
          <p>&copy; {currentYear} ConformIT. Tous droits réservés.</p>
          <p>
            Hébergement : Scaleway (Paris, France) • Plateforme conforme aux standards PCI-DSS &amp; ISO/IEC 27001.
          </p>
        </div>
      </div>
    </footer>
  )
}
