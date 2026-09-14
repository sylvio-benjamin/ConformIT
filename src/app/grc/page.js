'use client'

import { useEffect, useState } from 'react'
import { AlertTriangle, Shield, TrendingUp, AlertCircle, FileCheck, FileText, Plug, ArrowUp, ArrowDown, BarChart3 } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { grcAPI } from '@/services/api'
import Link from 'next/link'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Card from '@/components/Card'

export default function GRCDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    totalRisks: 0,
    criticalRisks: 0,
    totalControls: 0,
    activeControls: 0,
    totalKRIs: 0,
    activeKRIs: 0,
    totalIncidents: 0,
    openIncidents: 0,
    complianceScore: 0,
    totalReports: 0,
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) {
      setLoading(false)
      return
    }

    grcAPI.stats(user)
      .then((data) => setStats((prev) => ({ ...prev, ...data })))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [user])

  const statCards = [
    {
      title: 'Visualisations',
      value: '📊',
      subtitle: 'Graphiques & matrices',
      icon: BarChart3,
      color: 'bg-purple-500',
      href: '/vue',
    },
    {
      title: 'Risques',
      value: stats.totalRisks,
      subtitle: `${stats.criticalRisks || 0} critiques`,
      icon: AlertTriangle,
      color: 'bg-red-500',
      href: '/risques',
    },
    {
      title: 'Contrôles',
      value: stats.totalControls,
      subtitle: `${stats.activeControls} actifs`,
      icon: Shield,
      color: 'bg-blue-500',
      href: '/controles',
    },
    {
      title: 'KRIs',
      value: stats.totalKRIs,
      subtitle: `${stats.activeKRIs} actifs`,
      icon: TrendingUp,
      color: 'bg-green-500',
      href: '/grc/kris',
    },
    {
      title: 'Incidents',
      value: stats.totalIncidents,
      subtitle: `${stats.openIncidents} ouverts`,
      icon: AlertCircle,
      color: 'bg-orange-500',
      href: '/grc/incidents',
    },
    {
      title: 'Conformité',
      value: `${stats.complianceScore}%`,
      subtitle: 'Score global',
      icon: FileCheck,
      color: 'bg-purple-500',
      href: '/conformite',
    },
    {
      title: 'Rapports',
      value: stats.totalReports,
      subtitle: 'Générés',
      icon: FileText,
      color: 'bg-indigo-500',
      href: '/rapports',
    },
  ]

  if (loading) {
    return <LoadingSpinner message="Chargement du dashboard GRC..." />
  }

  return (
    <div className="p-8">
      <PageHeader
        title="Dashboard GRC"
        description="Vue d'ensemble de la gouvernance, des risques et de la conformité"
      />

      {/* Stats Grid */}
      <div className="mb-8 flex flex-wrap justify-center gap-6">
        {statCards.map((card) => {
          const Icon = card.icon
          return (
            <Link
              key={card.title}
              href={card.href}
              className="w-full md:w-[calc(50%-0.75rem)] lg:w-[calc(33.333%-1rem)]"
            >
              <Card hover className="h-full">
                <div className="flex items-center justify-between mb-4">
                  <div className={`${card.color} p-3 rounded-lg text-white`}>
                    <Icon className="h-6 w-6" />
                  </div>
                  <ArrowUp className="h-5 w-5 text-gray-400" />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-1">{card.value}</h3>
                <p className="text-sm font-medium text-gray-700 mb-1">{card.title}</p>
                <p className="text-xs text-gray-500">{card.subtitle}</p>
              </Card>
            </Link>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        {/* Recent Risks */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Risques récents</h2>
          <div className="space-y-3">
            <p className="text-sm text-gray-500">Aucun risque récent</p>
            <Link
              href="/risques"
              className="text-sm text-[#003366] hover:text-[#00A859] font-medium"
            >
              Voir tous les risques →
            </Link>
          </div>
        </Card>

        {/* Recent Incidents */}
        <Card>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Incidents récents</h2>
          <div className="space-y-3">
            <p className="text-sm text-gray-500">Aucun incident récent</p>
            <Link
              href="/grc/incidents"
              className="text-sm text-[#003366] hover:text-[#00A859] font-medium"
            >
              Voir tous les incidents →
            </Link>
          </div>
        </Card>
      </div>

      {/* Compliance Status */}
      <Card>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">État de conformité</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">ISO 31000</span>
            <span className="text-sm text-gray-500">Non évalué</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">ISO 27005</span>
            <span className="text-sm text-gray-500">Non évalué</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">COSO ERM</span>
            <span className="text-sm text-gray-500">Non évalué</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">COBIT</span>
            <span className="text-sm text-gray-500">Non évalué</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">SOX</span>
            <span className="text-sm text-gray-500">Non évalué</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">RGPD</span>
            <span className="text-sm text-gray-500">Non évalué</span>
          </div>
          <Link
            href="/conformite"
            className="block mt-4 text-sm text-[#003366] hover:text-[#00A859] font-medium text-center"
          >
            Évaluer la conformité →
          </Link>
        </div>
      </Card>
    </div>
  )
}

