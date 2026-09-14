'use client'

import NavbarAdmin from '@/app/components/NavbarAdmin'
import { useState } from 'react'

export default function AddUserForm() {
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    email: '',
    motDePasse: 'Temp@1234',
    admin: false
  })

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    try {
      const api = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const res = await fetch(`${api}/api/v1/admin/users`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: formData.email,
          nom: formData.nom,
          prenom: formData.prenom,
          admin: formData.admin,
          password: formData.motDePasse,
        }),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) {
        throw new Error(data.detail || 'Erreur lors de la création')
      }

      setSuccess(
        'Utilisateur ajouté. Il pourra se connecter avec le mot de passe temporaire, puis le changer.'
      )
      setFormData({
        nom: '',
        prenom: '',
        email: '',
        motDePasse: 'Temp@1234',
        admin: false
      })
    } catch (err) {
      console.error('❌ Erreur :', err)
      setError(err.message || 'Erreur lors de la création')
    }
  }

  return (
    <>
      <NavbarAdmin />
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md">
          <h1 className="text-2xl font-bold mb-6 text-center">Ajouter un utilisateur</h1>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <input
              type="text"
              placeholder="Nom"
              value={formData.nom}
              onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
              required
              className="border rounded px-4 py-2"
            />
            <input
              type="text"
              placeholder="Prénom"
              value={formData.prenom}
              onChange={(e) => setFormData({ ...formData, prenom: e.target.value })}
              required
              className="border rounded px-4 py-2"
            />
            <input
              type="email"
              placeholder="Email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              required
              className="border rounded px-4 py-2"
            />

            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={formData.admin}
                onChange={(e) => setFormData({ ...formData, admin: e.target.checked })}
              />
              Utilisateur administrateur ?
            </label>

            {error && <p className="text-red-500 text-sm">{error}</p>}
            {success && <p className="text-green-600 text-sm">{success}</p>}

            <button
              type="submit"
              className="bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
            >
              Ajouter
            </button>
          </form>
        </div>
      </div>
    </>
  )
}