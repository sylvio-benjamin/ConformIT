'use client'

import { Fragment, useEffect, useMemo, useState } from 'react'
import {
  AlertCircle,
  Bell,
  CloudDownload,
  FileText,
  Globe,
  Key,
  KeyRound,
  LockKeyhole,
  LogOut,
  Trash2,
  UserCircle
} from 'lucide-react'
import { Dialog, Transition } from '@headlessui/react'
import NavUtilisateur from '@/components/NavUtilisateur'
import { useAuth } from '@/hooks/useAuth'
import { usersAPI } from '@/services/api'
import { authClient } from '@/services/authClient'
import { toast } from 'react-hot-toast'
import Link from 'next/link'
import { exportUserData, fetchSessions, revokeSessions, updatePreferences } from '@/services/userSettings'
import LoadingSpinner from '@/components/LoadingSpinner'
import PageHeader from '@/components/PageHeader'
import Button from '@/components/Button'
import Card from '@/components/Card'

const defaultPreferences = {
  notifications: { email: true },
  language: 'fr',
  two_factor_enabled: false
}

export default function ParametresPage() {
  const { user } = useAuth()
  const [settings, setSettings] = useState(null)
  const [loadingSettings, setLoadingSettings] = useState(true)
  const [profileModalOpen, setProfileModalOpen] = useState(false)
  const [securityModalOpen, setSecurityModalOpen] = useState(false)
  const [sessionsModalOpen, setSessionsModalOpen] = useState(false)
  const [sessions, setSessions] = useState(null)
  const [sessionsLoading, setSessionsLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [passwordSaving, setPasswordSaving] = useState(false)
  const [profileForm, setProfileForm] = useState({
    nom: '',
    prenom: '',
    email: '',
    entreprise: '',
    telephone: '',
    currentPassword: ''
  })
  const [securityForm, setSecurityForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [preferences, setPreferences] = useState(defaultPreferences)
  const [updatingPreferences, setUpdatingPreferences] = useState(false)
  const [twoFactorLoading, setTwoFactorLoading] = useState(false)

  useEffect(() => {
    if (!user) {
      setLoadingSettings(false)
      return
    }
    usersAPI.getCurrentUser(user)
      .then((data) => {
        setSettings(data)
        const prefs = {
          ...defaultPreferences,
          ...(data.preferences || {})
        }
        prefs.notifications = {
          ...defaultPreferences.notifications,
          ...(prefs.notifications || {})
        }
        setPreferences(prefs)
      })
      .catch(() => setSettings(user))
      .finally(() => setLoadingSettings(false))
  }, [user])

  // Dès que la modale s'ouvre, préremplir le formulaire
  useEffect(() => {
    if (!profileModalOpen || !settings) return
    setProfileForm(form => ({
      ...form,
      nom: settings.nom || '',
      prenom: settings.prenom || '',
      email: settings.email || user?.email || '',
      entreprise: settings.entreprise || '',
      telephone: settings.telephone || '',
      currentPassword: ''
    }))
  }, [profileModalOpen, settings])

  const notificationsEmail = preferences.notifications?.email ?? true
  const language = preferences.language || 'fr'
  const isTwoFactorEnabled = preferences.two_factor_enabled || false

  const handleProfileSave = async () => {
    if (!user?.uid) return

    setSaving(true)
    try {
      const data = await usersAPI.updateProfile(user, {
        nom: profileForm.nom,
        prenom: profileForm.prenom,
        entreprise: profileForm.entreprise || null,
        telephone: profileForm.telephone || null,
      })
      setSettings((prev) => ({ ...prev, ...data }))
      toast.success('Informations mises à jour')
      setProfileModalOpen(false)
    } catch (error) {
      console.error('Erreur mise à jour profil', error)
      toast.error(error.message || "Impossible de mettre à jour vos informations.")
    } finally {
      setSaving(false)
    }
  }

  const handlePasswordChange = async () => {
    if (!user?.uid) return

    if (!securityForm.currentPassword || !securityForm.newPassword) {
      toast.error('Veuillez remplir tous les champs.')
      return
    }
    if (securityForm.newPassword !== securityForm.confirmPassword) {
      toast.error('Les mots de passe ne correspondent pas.')
      return
    }
    if (securityForm.newPassword.length < 8) {
      toast.error('Le mot de passe doit contenir au moins 8 caractères.')
      return
    }

    setPasswordSaving(true)
    try {
      await authClient.changePassword(securityForm.currentPassword, securityForm.newPassword)
      toast.success('Mot de passe mis à jour')
      setSecurityForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      })
      setSecurityModalOpen(false)
    } catch (error) {
      console.error('Erreur modification mot de passe', error)
      toast.error(error.message || 'Impossible de modifier le mot de passe.')
    } finally {
      setPasswordSaving(false)
    }
  }

  const persistPreferences = async (newPrefs) => {
    if (!user?.uid) return
    setUpdatingPreferences(true)
    try {
      const merged = {
        ...defaultPreferences,
        ...(preferences || {}),
        ...newPrefs
      }
      merged.notifications = {
        ...defaultPreferences.notifications,
        ...(preferences?.notifications || {}),
        ...(newPrefs.notifications || {})
      }
      await updatePreferences(user.uid, merged)
      setPreferences(merged)
    } catch (error) {
      console.error('Erreur preferences', error)
      toast.error(error.message || 'Impossible de mettre à jour vos préférences.')
    } finally {
      setUpdatingPreferences(false)
    }
  }

  const toggleNotifications = () => {
    persistPreferences({
      notifications: { email: !notificationsEmail }
    })
  }

  const changeLanguage = (value) => {
    persistPreferences({ language: value })
  }

  const toggleTwoFactor = async () => {
    if (!user?.uid) return
    setTwoFactorLoading(true)
    try {
      await persistPreferences({
        two_factor_enabled: !isTwoFactorEnabled
      })
      toast.success(!isTwoFactorEnabled ? '2FA activée (préférence)' : '2FA désactivée')
    } catch (error) {
      // persistPreferences affiche déjà l'erreur
    } finally {
      setTwoFactorLoading(false)
    }
  }

  const handleExport = async () => {
    if (!user?.uid) return
    try {
      await exportUserData(user.uid)
      toast.success('Export en cours de téléchargement')
    } catch (error) {
      console.error('Erreur export', error)
      toast.error(error.message || "Impossible d'exporter vos données.")
    }
  }

  const openSessionsModal = async () => {
    if (!user?.uid) return
    setSessionsLoading(true)
    setSessionsModalOpen(true)
    try {
      const data = await fetchSessions(user.uid)
      setSessions(data)
    } catch (error) {
      console.error('Erreur récupération sessions', error)
      toast.error(error.message || 'Impossible de récupérer les sessions.')
    } finally {
      setSessionsLoading(false)
    }
  }

  const handleRemoteLogout = async () => {
    if (!user?.uid) return
    setSessionsLoading(true)
    try {
      await revokeSessions(user.uid)
      toast.success('Toutes les sessions ont été déconnectées.')
      const data = await fetchSessions(user.uid)
      setSessions(data)
    } catch (error) {
      console.error('Erreur déconnexion distante', error)
      toast.error(error.message || 'Impossible de déconnecter vos sessions.')
    } finally {
      setSessionsLoading(false)
    }
  }

  const planLabel = useMemo(() => {
    const plan = settings?.abonnement || 'basic'
    if (plan === 'pro') return 'Pro'
    if (plan === 'enterprise') return 'Business'
    return 'Basique'
  }, [settings?.abonnement])

  const renderSessions = () => {
    if (sessionsLoading) {
      return <p className="text-sm text-gray-500">Chargement des sessions...</p>
    }
    if (!sessions) {
      return <p className="text-sm text-gray-500">Aucune information de session disponible.</p>
    }
    return (
      <div className="space-y-3">
        <div className="text-sm text-gray-600">
          <p><strong>Dernière connexion :</strong> {sessions.last_sign_in ? new Date(sessions.last_sign_in).toLocaleString() : '—'}</p>
          <p><strong>Tokens valides depuis :</strong> {sessions.tokens_valid_after ? new Date(sessions.tokens_valid_after).toLocaleString() : '—'}</p>
        </div>
        <div className="space-y-2">
          {sessions.sessions && sessions.sessions.length > 0 ? sessions.sessions.map((session, idx) => (
            <div key={idx} className="border rounded-lg p-3">
              <p className="font-semibold text-gray-700">{session.device || 'Appareil inconnu'}</p>
              <p className="text-sm text-gray-500">Dernière activité : {session.last_activity ? new Date(session.last_activity).toLocaleString() : '—'}</p>
            </div>
          )) : (
            <p className="text-sm text-gray-500">Aucune session active détectée.</p>
          )}
        </div>
        <button
          onClick={handleRemoteLogout}
          disabled={sessionsLoading}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:cursor-not-allowed disabled:bg-red-300"
        >
          <LogOut size={16} /> Déconnexion à distance
        </button>
      </div>
    )
  }

  if (loadingSettings) {
    return (
      <div className="min-h-screen bg-gray-50">
        <NavUtilisateur />
        <LoadingSpinner message="Chargement des paramètres..." />
      </div>
    )
  }

  return (
    <>
    <div className="min-h-screen bg-gray-50">
      <NavUtilisateur />
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <PageHeader
            title="Paramètres du compte"
            description="Gérez vos informations personnelles, votre sécurité et vos préférences"
          />

          <div className="space-y-6">
            {/* Informations personnelles */}
            <Card>
              <Section
                icon={<UserCircle className="text-blue-600" />}
                title="Informations personnelles"
                subtitle="Gérez votre nom et votre adresse email"
              >
                <Button variant="outline" size="sm" onClick={() => setProfileModalOpen(true)}>
                  Modifier mes informations
                </Button>
              </Section>
            </Card>

            {/* Sécurité */}
            <Card>
              <Section
                icon={<Key className="text-indigo-600" />}
                title="Sécurité du compte"
                subtitle="Changez votre mot de passe ou activez la 2FA"
              >
                <div className="flex items-center gap-4">
                  <Button variant="outline" size="sm" onClick={() => setSecurityModalOpen(true)}>
                    Modifier mon mot de passe
                  </Button>
                  <Button
                    variant={isTwoFactorEnabled ? 'success' : 'outline'}
                    size="sm"
                    onClick={toggleTwoFactor}
                    disabled={twoFactorLoading}
                  >
                    <KeyRound className="h-4 w-4 mr-2" />
                    {isTwoFactorEnabled ? '2FA activée' : 'Activer la 2FA'}
                  </Button>
                </div>
              </Section>
            </Card>

            <Card>
              <ToggleSetting
                icon={<Bell className="text-blue-600" />}
                title="Notifications email"
                description="Recevez des alertes pour chaque analyse critique ou action importante"
                checked={notificationsEmail}
                onChange={toggleNotifications}
                disabled={updatingPreferences}
              />
            </Card>

            <Card>
              <Section
                icon={<Globe className="text-green-600" />}
                title="Langue et préférences"
                subtitle="Choisissez la langue par défaut de l'interface"
              >
                <select
                  value={language}
                  onChange={(event) => changeLanguage(event.target.value)}
                  disabled={updatingPreferences}
                  className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366]"
                >
                  <option value="fr">Français</option>
                  <option value="en">English</option>
                </select>
              </Section>
            </Card>

            <Card>
              <Section
                icon={<FileText className="text-yellow-500" />}
                title="Plan d'abonnement"
                subtitle="La facturation n’est pas activée. L’abonnement n’est pas proposé pour l’instant."
              >
                <p className="text-sm text-gray-500">Aucune action requise.</p>
              </Section>
            </Card>

            <Card>
              <Section
                icon={<CloudDownload className="text-gray-600" />}
                title="Exporter mes données"
                subtitle="Téléchargez toutes vos données personnelles (RGPD)"
              >
                <Button variant="outline" size="sm" onClick={handleExport}>
                  Exporter
                </Button>
              </Section>
            </Card>

            <Card>
              <Section
                icon={<LogOut className="text-red-500" />}
                title="Sessions actives"
                subtitle="Déconnectez-vous de tous les appareils"
              >
                <Button variant="outline" size="sm" onClick={openSessionsModal}>
                  Voir les sessions
                </Button>
              </Section>
            </Card>

            <Card>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Trash2 className="text-red-500" size={22} />
                  <div>
                    <h2 className="text-lg font-semibold text-red-600">Supprimer mon compte</h2>
                    <p className="text-sm text-red-400">
                      Action irréversible. Vos données seront définitivement supprimées.
                    </p>
                  </div>
                </div>
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => toast('La suppression de compte sera bientôt disponible.', { icon: 'ℹ️' })}
                >
                  Supprimer
                </Button>
              </div>
            </Card>
          </div>
        </div>
      </main>
    </div>

      <ProfileModal
        open={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        form={profileForm}
        setForm={setProfileForm}
        onSave={handleProfileSave}
        saving={saving}
      />

      <SecurityModal
        open={securityModalOpen}
        onClose={() => setSecurityModalOpen(false)}
        form={securityForm}
        setForm={setSecurityForm}
        onSave={handlePasswordChange}
        saving={passwordSaving}
      />

      <SessionsModal
        open={sessionsModalOpen}
        onClose={() => setSessionsModalOpen(false)}
        renderContent={renderSessions}
      />
    </>
)}

function ToggleSetting({ icon, title, description, checked, onChange, disabled }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        {icon}
        <div>
          <h2 className="text-lg font-medium">{title}</h2>
          <p className="text-sm text-gray-500">{description}</p>
        </div>
      </div>
      <label className="inline-flex cursor-pointer items-center gap-2">
        <span className="text-xs text-gray-400">{checked ? 'Oui' : 'Non'}</span>
        <input
          type="checkbox"
          className="h-5 w-5 accent-blue-600"
          checked={checked}
          onChange={onChange}
          disabled={disabled}
        />
      </label>
    </div>
  )
}

function Section({ icon, title, subtitle, children }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-4">
        {icon}
        <div>
          <h2 className="text-lg font-medium">{title}</h2>
          {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
        </div>
      </div>
      {children}
    </div>
  )
}

function ProfileModal({ open, onClose, form, setForm, onSave, saving }) {
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-900/40" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-6">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-white p-6 text-left align-middle shadow-xl">
                <Dialog.Title className="text-lg font-semibold text-gray-800">
                  Modifier mes informations
                </Dialog.Title>
                <p className="mt-1 text-sm text-gray-500">
                  Les modifications d’email nécessitent la confirmation de votre mot de passe actuel.
                </p>
                <form
                  onSubmit={(event) => {
                    event.preventDefault()
                    onSave()
                  }}
                  className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2"
                >
                  <InputField
                    label="Prénom"
                    value={form.prenom}
                    onChange={(value) => setForm(prev => ({ ...prev, prenom: value }))}
                  />
                  <InputField
                    label="Nom"
                    value={form.nom}
                    onChange={(value) => setForm(prev => ({ ...prev, nom: value }))}
                  />
                  <InputField
                    label="Entreprise"
                    value={form.entreprise}
                    onChange={(value) => setForm(prev => ({ ...prev, entreprise: value }))}
                  />
                  <InputField
                    label="Téléphone"
                    value={form.telephone}
                    onChange={(value) => setForm(prev => ({ ...prev, telephone: value }))}
                  />
                  <InputField
                    label="Adresse email"
                    value={form.email}
                    type="email"
                    className="sm:col-span-2"
                    onChange={(value) => setForm(prev => ({ ...prev, email: value }))}
                  />
                  <InputField
                    label="Mot de passe actuel"
                    type="password"
                    hint="Requis si vous changez votre adresse email."
                    className="sm:col-span-2"
                    value={form.currentPassword}
                    onChange={(value) => setForm(prev => ({ ...prev, currentPassword: value }))}
                  />
                  <div className="sm:col-span-2 mt-2 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={onClose}
                      className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
                    >
                      Annuler
                    </button>
                    <button
                      type="submit"
                      disabled={saving}
                      className="rounded bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
                    >
                      {saving ? 'Enregistrement...' : 'Enregistrer'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}

function SecurityModal({ open, onClose, form, setForm, onSave, saving }) {
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-900/40" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-6">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white p-6 text-left shadow-xl transition-all">
                <Dialog.Title className="text-lg font-semibold text-gray-800">
                  Modifier mon mot de passe
                </Dialog.Title>
                <p className="mt-1 text-sm text-gray-500">
                  Pour garantir votre sécurité, nous vous demanderons de confirmer votre mot de passe actuel.
                </p>
                <form
                  onSubmit={(event) => {
                    event.preventDefault()
                    onSave()
                  }}
                  className="mt-4 space-y-4"
                >
                  <InputField
                    label="Mot de passe actuel"
                    type="password"
                    value={form.currentPassword}
                    onChange={(value) => setForm(prev => ({ ...prev, currentPassword: value }))}
                    autoComplete="current-password"
                  />
                  <InputField
                    label="Nouveau mot de passe"
                    type="password"
                    value={form.newPassword}
                    onChange={(value) => setForm(prev => ({ ...prev, newPassword: value }))}
                    autoComplete="new-password"
                    hint="Minimum 8 caractères, avec majuscules/minuscules et chiffres."
                  />
                  <InputField
                    label="Confirmer le mot de passe"
                    type="password"
                    value={form.confirmPassword}
                    onChange={(value) => setForm(prev => ({ ...prev, confirmPassword: value }))}
                    autoComplete="new-password"
                  />

                  <div className="mt-2 flex justify-end gap-3">
                    <button
                      type="button"
                      onClick={onClose}
                      className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
                    >
                      Annuler
                    </button>
                    <button
                      type="submit"
                      disabled={saving}
                      className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300"
                    >
                      {saving ? 'Enregistrement...' : 'Mettre à jour'}
                    </button>
                  </div>
                </form>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}

function SessionsModal({ open, onClose, renderContent }) {
  return (
    <Transition.Root show={open} as={Fragment}>
      <Dialog as="div" className="relative z-10" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-200"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-150"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-900/40" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4 text-center sm:p-6">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-200"
              enterFrom="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
              enterTo="opacity-100 translate-y-0 sm:scale-100"
              leave="ease-in duration-150"
              leaveFrom="opacity-100 translate-y-0 sm:scale-100"
              leaveTo="opacity-0 translate-y-4 sm:translate-y-0 sm:scale-95"
            >
              <Dialog.Panel className="w-full max-w-lg transform overflow-hidden rounded-2xl bg-white p-6 text-left shadow-xl transition-all">
                <Dialog.Title className="text-lg font-semibold text-gray-800">
                  Sessions actives
                </Dialog.Title>
                <p className="mt-1 text-sm text-gray-500">
                  Vous pouvez consulter vos connexions récentes et forcer la déconnexion sur tous vos appareils.
                </p>
                <div className="mt-4">{renderContent()}</div>
                <div className="mt-6 flex justify-end">
                  <button
                    onClick={onClose}
                    className="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-100"
                  >
                    Fermer
                  </button>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  )
}

function InputField({ label, value, onChange, type = 'text', hint, className = '', autoComplete }) {
  return (
    <label className={`flex flex-col text-sm text-gray-700 ${className}`}>
      <span className="font-semibold">{label}</span>
      <input
        type={type}
        value={value || ''}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
        className="mt-1 rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
      {hint && <span className="mt-1 text-xs text-gray-400">{hint}</span>}
    </label>
  )
}
