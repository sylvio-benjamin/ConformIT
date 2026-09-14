'use client'

import { useEffect, useState } from 'react'
import { Eye, Trash2, FileEdit, Building2, User, ChevronDown, Download, FileSpreadsheet } from 'lucide-react'
import Upload from '../components/Upload'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { authClient } from '@/services/authClient'
import toast from 'react-hot-toast'
import { useAuth } from '@/hooks/useAuth'
import { useAnalyses } from '@/hooks/useAnalyses'
import { analysesAPI } from '@/services/api'
import NavUtilisateur from '@/components/NavUtilisateur'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import ScoreBadge from '@/components/ScoreBadge'
import RiskBadge from '@/components/RiskBadge'
import { Button } from '@/components/ui/button'
import PageContainer from '@/components/PageContainer'
import MainContent from '@/components/MainContent'
import StatCard from '@/components/StatCard'
import { Search } from 'lucide-react'
import { RISK_FILTERS, matchesRiskFilter } from '@/lib/riskLabels'

export default function EmployePage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const { analyses: analysesData, loading: analysesLoading, error: analysesError, deleteAnalysis } = useAnalyses();
  const [recherche, setRecherche] = useState('');
  const [filtreStatut, setFiltreStatut] = useState('Tous');
  const [page, setPage] = useState(1);
  const [recentJobs, setRecentJobs] = useState([]);
  const analysesParPage = 5;

  useEffect(() => {
    if (!user) return undefined;
    let cancelled = false;
    analysesAPI.listJobs()
      .then((data) => {
        if (!cancelled) setRecentJobs(Array.isArray(data?.jobs) ? data.jobs.slice(0, 5) : []);
      })
      .catch(() => {
        if (!cancelled) setRecentJobs([]);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleLogout = async () => {
    try {
      await authClient.logout();
      router.push('/');
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
    }
  };

  // Transformer les données de l'API en format compatible
  const analyses = analysesData.map(a => ({
    id: a.analysis_number || a.id || a.slug,  // Utiliser le numéro d'analyse (1, 2, 3, etc.)
    analysis_number: a.analysis_number,  // Numéro d'analyse pour l'affichage
    slug: a.slug,
    nom: a.nom || a.nom_entreprise || '',
    nomFichier: a.nom_fichier || a.filename || '—',
    rcs: a.rcs || a.RCS || '—',
    risque: a.risque || a.niveau_risque || 'En attente',
    precision: a.precision || '',
    statut: a.status || a.statut || 'En attente',
    date: a.date || a.created_at || a.date_creation || '',
    id_employe: user?.uid || '',
    score: a.score || a.score_total || 0,
    riskColor: a.risk_color || '',
    documentType: a.type || a.type_document || a.document_type || '—'
  }));

  const total = analyses.length;
  const scoreAverage = total ? Math.round(analyses.reduce((sum, a) => sum + (Number(a.score) || 0), 0) / total) : 0;
  const criticalCount = analyses.filter(a => (Number(a.score) || 0) >= 75).length;

  const analysesFiltrees = analyses
    .filter((a) =>
      (a.nom.toLowerCase().includes(recherche.toLowerCase()) || String(a.rcs).includes(recherche)) &&
      matchesRiskFilter(a.risque, filtreStatut)
    )
    .sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')));

  const totalPages = Math.ceil(analysesFiltrees.length / analysesParPage);
  const analysesPage = analysesFiltrees.slice((page - 1) * analysesParPage, page * analysesParPage);

  function toSlug(nom) {
    return nom
      .toLowerCase()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/\s+/g, '_')
      .replace(/[^a-z0-9_-]/g, '');
  }

  function handleDownload(nom, type = 'pdf') {
    const slug = toSlug(nom)
    const endpoint = type === 'excel' ? 'telecharger-excel' : 'telecharger-pdf'
    let url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/${endpoint}/${slug}`
    
    if (user?.uid) {
      url += `?user_id=${user.uid}`
    }
    
    window.open(url, '_blank')
  }

  const handleDelete = async (analyse) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer l'analyse de "${analyse.nom}" (score : ${analyse.score}/100) ?`)) {
      return;
    }
  
    const slug = analyse.slug || toSlug(analyse.nom);
    
    if (!slug) {
      toast.error("Impossible de supprimer cette analyse : slug invalide");
      return;
    }
  
    try {
      // Supprimer les fichiers via l'API backend
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/supprimer-fichiers/${slug}`, {
        method: 'DELETE',
      });
  
      // Supprimer l'analyse via l'API PostgreSQL
      await deleteAnalysis(slug);
      
      toast.success(`Analyse de "${analyse.nom}" supprimée avec succès`);
      router.refresh();
    } catch (error) {
      console.error("Erreur lors de la suppression :", error);
      toast.error("Une erreur est survenue lors de la suppression.");
    }
  };

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-gray-50">
        <NavUtilisateur />
        <LoadingSpinner message="Chargement..." />
      </div>
    )
  }

  if (analysesLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <NavUtilisateur />
        <div className="flex min-h-screen flex-col items-center justify-center gap-6">
          <LoadingSpinner message="Chargement des données..." />
          <button
            onClick={() => window.location.reload()}
            className="bg-[#003366] hover:bg-[#004080] text-white font-semibold px-6 py-3 rounded-xl shadow-lg transition text-lg"
          >
            Revenir à l&apos;espace employé
          </button>
          <span className="text-gray-400 text-sm">L&apos;analyse continue en arrière-plan.</span>
        </div>
      </div>
    )
  }

  return (
    <PageContainer>
      <NavUtilisateur />
      <MainContent>
        <PageHeader
          title="Analyses"
          description="Dépôt, suivi des jobs, résultats et exports — l’historique est un simple tri par date"
        />

        {recentJobs.length > 0 && (
          <div className="mb-6 bg-white rounded-xl shadow-md p-4">
            <h2 className="text-sm font-semibold text-gray-700 mb-3">Jobs récents</h2>
            <ul className="space-y-2">
              {recentJobs.map((job) => (
                <li key={job.id} className="flex flex-wrap items-center justify-between gap-2 text-sm">
                  <span className="text-gray-800">{job.filename || job.slug || 'Document'}</span>
                  <span className={
                    job.status === 'failed'
                      ? 'text-red-600'
                      : job.status === 'running' || job.status === 'queued'
                        ? 'text-amber-600'
                        : 'text-green-700'
                  }>
                    {job.status === 'running' && 'En cours'}
                    {job.status === 'queued' && 'En file'}
                    {job.status === 'completed' && 'Terminé'}
                    {job.status === 'failed' && 'Échec'}
                    {job.status === 'cancelled' && 'Annulé'}
                    {!['running', 'queued', 'completed', 'failed', 'cancelled'].includes(job.status) && job.status}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <StatCard
              title="Total des analyses"
              value={total}
              color="blue"
            />
            <StatCard
              title="Score moyen risque"
              value={`${scoreAverage}/100`}
              subtitle={`${criticalCount} critiques`}
              color="orange"
            />
            <StatCard
              title="Analyses critiques"
              value={criticalCount}
              subtitle="Score > 80"
              color="red"
            />
          </div>

          {/* Filters */}
          <div className="mb-6 flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Rechercher par nom ou numéro de SIRET…"
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent"
                value={recherche}
                onChange={e => setRecherche(e.target.value)}
              />
            </div>
            <select
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent"
              value={filtreStatut}
              onChange={e => setFiltreStatut(e.target.value)}
            >
              {RISK_FILTERS.map((option) => (
                <option key={option} value={option}>
                  {option === 'Tous' ? 'Tous les niveaux' : option}
                </option>
              ))}
            </select>
          </div>

        {/* Message d'erreur si problème de chargement */}
        {analysesError && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-red-800 font-medium">Erreur lors du chargement des analyses</p>
            <p className="text-red-600 text-sm mt-1">{analysesError}</p>
            <p className="text-red-500 text-xs mt-2">Vérifiez la console du navigateur pour plus de détails.</p>
          </div>
        )}

        {/* Table */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ENTREPRISES
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  FICHIER
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  RCS
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  SCORE
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  TYPE DOC
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  ACTIONS
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {analysesPage.length === 0 ? (
                <tr>
                  <td colSpan="8" className="px-6 py-4 text-center text-gray-500">
                    {analysesLoading ? 'Chargement...' : analysesError ? 'Erreur lors du chargement' : 'Aucune analyse trouvée'}
                  </td>
                </tr>
              ) : (
                analysesPage.map(e => (
                  <tr key={e.id} className="hover:bg-gray-50 transition">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{e.id}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-blue-500" />
                        <span className="text-sm font-medium text-gray-900">{e.nom}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {e.nomFichier && e.nomFichier !== '—' ? e.nomFichier : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {e.rcs || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {e.date ? new Date(e.date).toLocaleDateString('fr-FR') : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <ScoreBadge score={e.score} riskColor={e.riskColor} />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {e.documentType && e.documentType !== '—' ? e.documentType : '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex justify-center gap-2">
                        <button
                          title="Modifier"
                          className="text-orange-500 hover:text-orange-700 transition"
                          onClick={() => {
                            if (typeof window !== 'undefined') {
                              if (e.slug) {
                                localStorage.setItem('slug', e.slug)
                              }
                              localStorage.setItem('analyseId', String(e.id))
                            }
                            router.push(`/employe/resultat-analyse/modification${e.slug ? `?slug=${e.slug}` : ''}`)
                          }}
                        >
                          <FileEdit className="h-5 w-5" />
                        </button>
                        <button
                          title="Voir"
                          className="text-blue-600 hover:text-blue-800 transition"
                          onClick={() => {
                            const slugToUse = e.slug || toSlug(e.nom)
                            if (typeof window !== 'undefined' && slugToUse) {
                              localStorage.setItem('slug', slugToUse)
                            }
                            router.push(`/employe/entreprise?slug=${slugToUse || e.id}`)
                          }}
                        >
                          <Eye className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDownload(e.nom)}
                          title="Télécharger"
                          className="text-green-600 hover:text-green-800 transition"
                        >
                          <Download className="h-5 w-5" />
                        </button>
                        <button
                          onClick={() => handleDownload(e.nom, 'excel')}
                          title="Télécharger en Excel"
                          className="text-emerald-600 hover:text-emerald-800 transition"
                        >
                          <FileSpreadsheet className="h-5 w-5" />
                        </button>
                        <button
                          title="Supprimer"
                          className="text-red-600 hover:text-red-800 transition"
                          onClick={() => handleDelete(e)}
                        >
                          <Trash2 className="h-5 w-5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center items-center gap-4 px-6 py-4 border-t border-gray-200">
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                Précédent
              </Button>
              <span className="text-sm text-gray-600">Page {page} / {totalPages}</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setPage(page + 1)}
                disabled={page === totalPages}
              >
                Suivant
              </Button>
            </div>
          )}
        </div>

        {/* Upload */}
        <div className="mt-6 flex justify-center">
          <Upload analysesEmploye={analyses} />
        </div>
      </MainContent>
    </PageContainer>
  );
}