'use client'

import Link from 'next/link'
import { Menu } from '@headlessui/react'
import { ChevronDown, User } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { usePathname, useRouter } from 'next/navigation'

const NAV = [
  { href: '/vue', label: 'Vue d’ensemble', match: (path) => path === '/vue' || path === '/employe/dashboard' },
  { href: '/analyses', label: 'Analyses', match: (path) => path.startsWith('/analyses') || path.startsWith('/employe') || path === '/historique' },
  { href: '/risques', label: 'Risques', match: (path) => path.startsWith('/risques') || path.startsWith('/grc/risks') },
  { href: '/controles', label: 'Contrôles', match: (path) => path.startsWith('/controles') || path.startsWith('/grc/controls') },
  { href: '/conformite', label: 'Conformité', match: (path) => path.startsWith('/conformite') || path.startsWith('/grc/compliance') },
  { href: '/rapports', label: 'Rapports', match: (path) => path.startsWith('/rapports') || path.startsWith('/grc/reports') },
]

export default function EmployeeNavbar() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  const handleLogout = async () => {
    await logout()
    router.push('/')
  }

  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex w-full max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-4 lg:px-8">
        <div className="flex flex-wrap items-center gap-8">
          <Link href="/vue" className="flex items-center gap-3 text-gray-900">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#003366] text-sm font-semibold text-white">
              DA
            </div>
            <div className="leading-tight">
              <p className="text-sm font-semibold tracking-wide text-[#003366]">ConformIT</p>
              <p className="text-xs text-slate-500">Documents, preuves, conformité</p>
            </div>
          </Link>

          <nav className="flex flex-wrap items-center gap-5 text-sm font-medium text-slate-600">
            {NAV.map((item) => {
              const active = item.match(pathname || '')
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={active ? 'text-[#003366] font-semibold' : 'transition hover:text-[#003366]'}
                >
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          {user?.admin && (
            <Link href="/admin" className="text-sm font-medium text-slate-600 hover:text-[#003366]">
              Administration
            </Link>
          )}
          <div className="hidden text-right text-xs text-slate-500 sm:block">
            <p className="font-semibold text-slate-700">Connecté</p>
            <p>{user?.email || '—'}</p>
          </div>

          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-sm transition hover:border-blue-200 hover:text-[#003366]">
              <User className="h-4 w-4" />
              <span>Mon compte</span>
              <ChevronDown className="h-3 w-3" />
            </Menu.Button>
            <Menu.Items className="absolute right-0 z-20 mt-2 w-56 origin-top-right overflow-hidden rounded-lg border border-slate-200 bg-white shadow-lg focus:outline-none">
              <div className="py-1">
                <Menu.Item>
                  {({ active }) => (
                    <Link
                      href="/compte"
                      className={`block px-4 py-2 text-sm ${active ? 'bg-blue-50 text-[#003366]' : 'text-slate-700'}`}
                    >
                      Paramètres
                    </Link>
                  )}
                </Menu.Item>
                <Menu.Item>
                  {({ active }) => (
                    <button
                      onClick={() =>
                        confirm('Voulez-vous vraiment vous déconnecter ?') && handleLogout()
                      }
                      className={`block w-full px-4 py-2 text-left text-sm ${active ? 'bg-red-50 text-red-500' : 'text-red-500'}`}
                    >
                      Déconnexion
                    </button>
                  )}
                </Menu.Item>
              </div>
            </Menu.Items>
          </Menu>
        </div>
      </div>
    </header>
  )
}
