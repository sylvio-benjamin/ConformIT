'use client'

import { useEffect, useState } from 'react'
import { Eye, Trash2, FileEdit, Building2, Home, Users, Settings, LogOut, Plus } from 'lucide-react'
import Link from 'next/link'
import { authClient } from '@/services/authClient'
import { usePathname, useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import Input from '@/components/Input'

const STATUS_COLORS = {
  'En attente': 'bg-gray-100 text-gray-600',
  'Medium': 'bg-yellow-100 text-yellow-700',
  'High': 'bg-red-100 text-red-700',
  'Terminé': 'bg-green-100 text-green-700',
  'En cours': 'bg-blue-100 text-blue-700'
}

export default function PageUtilisateurs() {
  const pathname = usePathname()
  const router = useRouter()
  const [utilisateurs, setUtilisateurs] = useState([])
  const [chargement, setChargement] = useState(true)
  const [recherche, setRecherche] = useState('')
  const [filtreEntreprise, setFiltreEntreprise] = useState('Toutes')
  const [page, setPage] = useState(1)
  const utilisateursParPage = 10

  useEffect(() => {
    setChargement(true)
    const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    fetch(`${api}/api/v1/admin/users`, { credentials: 'include' })
      .then((res) => {
        if (!res.ok) throw new Error('Accès refusé')
        return res.json()
      })
      .then((data) => {
        const liste = (data.users || []).map((u) => ({
          id: u.id,
          nom: u.nom || '',
          prenom: u.prenom || '',
          matricule: u.id || '',
          entreprise: u.entreprise || '',
          role: u.admin ? 'Admin' : 'Employé',
        }))
        setUtilisateurs(liste)
      })
      .catch(() => setUtilisateurs([]))
      .finally(() => setChargement(false))
  }, [])

  const entreprises = ['Toutes', ...Array.from(new Set(utilisateurs.map((u) => u.entreprise).filter(Boolean)))]
  const utilisateursFiltres = utilisateurs.filter(
    (u) =>
      (filtreEntreprise === 'Toutes' || u.entreprise === filtreEntreprise) &&
      (u.nom.toLowerCase().includes(recherche.toLowerCase()) ||
        u.prenom.toLowerCase().includes(recherche.toLowerCase()) ||
        u.matricule.toLowerCase().includes(recherche.toLowerCase()))
  )
  const totalPages = Math.ceil(utilisateursFiltres.length / utilisateursParPage)
  const utilisateursPage = utilisateursFiltres.slice((page - 1) * utilisateursParPage, page * utilisateursParPage)

  const handleDelete = async (utilisateur) => {
    if (!window.confirm(`Supprimer ${utilisateur.nom} ${utilisateur.prenom} ?`)) return

    try {
      toast.error('La suppression admin sera branchée sur l’API (P2).')
      return
    } catch (error) {
      console.error('Erreur lors de la suppression:', error)
      toast.error('Erreur lors de la suppression')
    }
  }

  const handleLogout = async () => {
    if (!window.confirm('Voulez-vous vraiment vous déconnecter ?')) return
    try {
      await authClient.logout()
      router.push('/')
    } catch (err) {
      console.error('Erreur lors de la déconnexion :', err)
    }
  }

  if (chargement) {
    return (
      <div className="min-h-screen flex bg-gray-50">
        <LoadingSpinner message="Chargement des utilisateurs..." />
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
          title="Gestion des utilisateurs"
          description="Gérer les utilisateurs de la plateforme"
          action={
            <Link href="/admin/utilisateur/ajouter">
              <Button variant="primary" className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Ajouter un utilisateur
              </Button>
            </Link>
          }
        />

        {/* Filters */}
        <div className="mb-6 flex gap-4">
          <Input
            type="text"
            placeholder="Rechercher par nom, prénom ou matricule..."
            value={recherche}
            onChange={(e) => setRecherche(e.target.value)}
            className="flex-1"
          />
          <select
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
            value={filtreEntreprise}
            onChange={(e) => setFiltreEntreprise(e.target.value)}
          >
            {entreprises.map((ent) => (
              <option key={ent} value={ent}>
                {ent}
              </option>
            ))}
          </select>
        </div>

        {/* Table */}
        <div className="bg-white rounded-xl shadow-md overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nom
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Prénom
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Matricule
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entreprise
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Rôle
                </th>
                <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {utilisateursPage.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    Aucun utilisateur trouvé
                  </td>
                </tr>
              ) : (
                utilisateursPage.map((utilisateur) => (
                  <tr key={utilisateur.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {utilisateur.nom || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {utilisateur.prenom || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {utilisateur.matricule || '—'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-5 w-5 text-blue-500" />
                        <span className="text-sm text-gray-900">{utilisateur.entreprise || '—'}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-1 text-xs font-semibold rounded-full ${
                          utilisateur.role === 'Admin'
                            ? 'bg-purple-100 text-purple-700'
                            : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {utilisateur.role}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                      <div className="flex justify-center gap-2">
                        <Link
                          href={`/admin/utilisateur/modifier/${utilisateur.id}`}
                          className="text-blue-600 hover:text-blue-800 transition"
                          title="Modifier"
                        >
                          <FileEdit className="h-4 w-4" />
                        </Link>
                        <button
                          onClick={() => handleDelete(utilisateur)}
                          className="text-red-600 hover:text-red-800 transition"
                          title="Supprimer"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center items-center gap-4 mt-6">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page - 1)}
              disabled={page === 1}
            >
              Précédent
            </Button>
            <span className="text-gray-600">Page {page} / {totalPages}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(page + 1)}
              disabled={page === totalPages}
            >
              Suivant
            </Button>
          </div>
        )}
        </div>
      </main>
    </div>
  )
}
