'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter, usePathname } from 'next/navigation'
import { Home, Users, Settings, LogOut, BarChart2, UserCheck, ShieldAlert, Building2, FileEdit, Trash2 } from 'lucide-react'
import { authClient } from '@/services/authClient'

import GraphiqueNiveauxRisque from '../components/GraphiqueNiveauxRisque'
import ListeEntreprisesRisque from '../components/ListeEntreprisesRisque'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import { useAuth } from '@/hooks/useAuth'

export default function AdminDashboard() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  const handleLogout = async () => {
    if (!window.confirm('Voulez-vous vraiment vous déconnecter ?')) return
    try {
      await authClient.logout()
      router.push('/')
    } catch (err) {
      console.error('Erreur lors de la déconnexion :', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex bg-gray-50">
        <LoadingSpinner message="Chargement..." />
      </div>
    )
  }

  return (
    <div className="flex min-h-dvh bg-gray-50">
      <aside className="sticky top-0 flex h-dvh w-64 shrink-0 flex-col border-r border-gray-200 bg-white px-6 py-8 shadow-sm">
        <div className="mb-10">
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight mb-2">Administration</h2>
          <p className="text-sm text-gray-600">Back-office technique</p>
          <Link href="/vue" className="mt-3 inline-block text-sm font-medium text-[#003366]">
            Retour à ConformIT
          </Link>
        </div>
        <nav className="flex flex-col gap-2 flex-1">
          <Link
            href="/admin"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${
              pathname === '/admin'
                ? 'bg-[#003366] text-white font-semibold'
                : 'text-gray-700 hover:bg-gray-100 hover:text-[#003366]'
            }`}
          >
            <Home size={20} />
            Dashboard
          </Link>
          <Link
            href="/admin/utilisateur"
            className={`flex items-center gap-2 px-3 py-2 rounded-lg transition ${
              pathname === '/admin/utilisateur'
                ? 'bg-[#003366] text-white font-semibold'
                : 'text-gray-700 hover:bg-gray-100 hover:text-[#003366]'
            }`}
          >
            <Users size={20} />
            Utilisateurs
          </Link>
          <div className="mt-auto pt-8">
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 hover:text-red-700 transition w-full text-left"
            >
              <LogOut size={20} />
              Déconnexion
            </button>
          </div>
        </nav>
        <div className="mt-6 flex flex-col items-center gap-2 pt-6 border-t border-gray-200">
          <div className="w-12 h-12 rounded-full bg-[#003366] flex items-center justify-center text-xl font-bold text-white">
            A
          </div>
          <span className="text-xs text-gray-500">Administrateur</span>
        </div>
      </aside>

      {/* Main content */}
      <main className="min-w-0 flex-1">
        <div className="mx-auto w-full max-w-7xl p-8">
        <PageHeader
          title="Dashboard Administrateur"
          description={`Bienvenue, ${user?.email || 'Admin'}`}
        />

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div
            className="bg-white rounded-xl shadow-md p-6 flex flex-col items-center cursor-pointer hover:shadow-lg transition"
            onClick={() => router.push('/admin/utilisateur')}
            title="Voir les utilisateurs"
          >
            <UserCheck size={32} className="text-blue-500 mb-2" />
            <span className="text-3xl font-bold text-blue-700">42</span>
            <span className="text-gray-600 mt-2">Utilisateurs</span>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6 flex flex-col items-center">
            <BarChart2 size={32} className="text-green-500 mb-2" />
            <span className="text-3xl font-bold text-green-600">128</span>
            <span className="text-gray-600 mt-2">Analyses totales</span>
          </div>
          <div className="bg-white rounded-xl shadow-md p-6 flex flex-col items-center">
            <ShieldAlert size={32} className="text-orange-500 mb-2" />
            <span className="text-3xl font-bold text-orange-500">7</span>
            <span className="text-gray-600 mt-2">Entreprises à risque</span>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ListeEntreprisesRisque />
          <GraphiqueNiveauxRisque />
        </div>
        </div>
      </main>
    </div>
  )
}
