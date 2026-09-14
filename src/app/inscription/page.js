'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'react-hot-toast'
import { authClient } from '@/services/authClient'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Card from '@/components/Card'

export default function Inscription() {
  const router = useRouter()
  const [form, setForm] = useState({ nom: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    // Clear error when user starts typing
    if (errors[e.target.name]) {
      setErrors({ ...errors, [e.target.name]: '' })
    }
  }

  const validateForm = () => {
    const newErrors = {}
    if (!form.nom.trim()) {
      newErrors.nom = 'Le nom est requis'
    }
    if (!form.email.trim()) {
      newErrors.email = 'L\'email est requis'
    } else if (!/\S+@\S+\.\S+/.test(form.email)) {
      newErrors.email = 'L\'email n\'est pas valide'
    }
    if (!form.password) {
      newErrors.password = 'Le mot de passe est requis'
    } else if (form.password.length < 8) {
      newErrors.password = 'Le mot de passe doit contenir au moins 8 caractères'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validateForm()) {
      return
    }

    setLoading(true)
    try {
      await authClient.register({
        email: form.email,
        password: form.password,
        nom: form.nom,
      })
      toast.success('Compte créé avec succès !')
      router.push('/vue')
    } catch (error) {
      toast.error(error.message || 'Erreur lors de la création du compte')
      if (error.status === 409) {
        setErrors({ email: 'Cet email est déjà utilisé' })
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-50 px-4 py-10">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <p className="mb-2 text-sm font-semibold tracking-wide text-[#003366]">ConformIT</p>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Créer un compte</h1>
          <p className="text-gray-600">Rejoignez-nous pour commencer à analyser vos documents</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Nom complet"
            name="nom"
            type="text"
            placeholder="Votre nom complet"
            value={form.nom}
            onChange={handleChange}
            required
            error={errors.nom}
          />

          <Input
            label="Adresse email"
            name="email"
            type="email"
            placeholder="votre@email.com"
            value={form.email}
            onChange={handleChange}
            required
            error={errors.email}
          />

          <Input
            label="Mot de passe"
            name="password"
            type="password"
            placeholder="Minimum 8 caractères"
            value={form.password}
            onChange={handleChange}
            required
            error={errors.password}
          />

          <Button
            type="submit"
            disabled={loading}
            className="w-full"
            variant="primary"
          >
            {loading ? 'Création en cours...' : 'Créer un compte'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Déjà un compte ?{' '}
            <Link href="/" className="text-[#003366] hover:text-[#004080] font-medium">
              Se connecter
            </Link>
          </p>
        </div>
      </Card>
    </div>
  )
}
