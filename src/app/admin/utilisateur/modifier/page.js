'use client'

import { useState, useEffect } from 'react'
import NavbarAdmin from '../../../components/NavbarAdmin'

export default function EditUserForm({ user, onSave }) {
  const [formData, setFormData] = useState({
    nom: '',
    prenom: '',
    email: '',
    adresse: '',
  })

  useEffect(() => {
    if (user) {
      setFormData({
        nom: user.nom || '',
        prenom: user.prenom || '',
        email: user.email || '',
        adresse: user.adresse || '',
      })
    }
  }, [user])

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('Utilisateur modifié :', formData)
    if (onSave) onSave(formData)
  }

  return (
    <>
    <NavbarAdmin />
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-xl shadow-md w-full max-w-md text-center">
        <h1 className="text-2xl font-bold mb-6">Modifier un utilisateur</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Nom"
            value={formData.nom}
            onChange={(e) => setFormData({ ...formData, nom: e.target.value })}
            className="border rounded px-4 py-2 text-center"
            required
          />
          <input
            type="text"
            placeholder="Prénom"
            value={formData.prenom}
            onChange={(e) => setFormData({ ...formData, prenom: e.target.value })}
            className="border rounded px-4 py-2 text-center"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="border rounded px-4 py-2 text-center"
            required
          />
          <input
            type="text"
            placeholder="Adresse"
            value={formData.adresse}
            onChange={(e) => setFormData({ ...formData, adresse: e.target.value })}
            className="border rounded px-4 py-2 text-center"
            required
          />
          <button
            type="submit"
            className="bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition"
          >
            Sauvegarder
          </button>
        </form>
      </div>
    </div>
    </>
  )
}
