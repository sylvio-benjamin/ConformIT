'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { toast } from 'react-hot-toast'
import { authClient } from '@/services/authClient'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Card from '@/components/Card'

export default function LoginForm() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const router = useRouter()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const data = await authClient.login(email, password)
      toast.success('Connexion réussie !')
      if (data.user?.admin) {
        router.push('/admin')
      } else {
        router.push('/vue')
      }
    } catch (err) {
      const message = err.message || 'Email ou mot de passe incorrect'
      setError(message)
      toast.error(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-50 px-4 py-10">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <p className="mb-2 text-sm font-semibold tracking-wide text-[#003366]">ConformIT</p>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Connexion</h1>
          <p className="text-gray-600">Connectez-vous pour accéder à votre espace</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Adresse email"
            type="email"
            name="email"
            placeholder="votre@email.com"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              setError('')
            }}
            required
            error={error}
          />

          <Input
            label="Mot de passe"
            type="password"
            name="password"
            placeholder="Votre mot de passe"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              setError('')
            }}
            required
          />

          <div className="text-center">
            <Link
              href="/mdp-oublie"
              className="text-sm text-[#003366] hover:text-[#004080] font-medium"
            >
              Mot de passe oublié ?
            </Link>
          </div>

          <Button
            type="submit"
            disabled={loading}
            className="w-full justify-center"
            variant="primary"
          >
            {loading ? 'Connexion en cours...' : 'Se connecter'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Pas encore de compte ?{' '}
            <Link href="/inscription" className="text-[#003366] hover:text-[#004080] font-medium">
              Inscrivez-vous
            </Link>
          </p>
        </div>
      </Card>
    </div>
  )
}
