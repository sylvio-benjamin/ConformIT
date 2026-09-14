'use client'

import { useState } from 'react'
import Link from 'next/link'
import { authClient } from '@/services/authClient'
import Button from '@/components/Button'
import Input from '@/components/Input'
import Card from '@/components/Card'
import { toast } from 'react-hot-toast'

export default function MotDePasseOublie() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    if (!email.trim()) {
      setError('Veuillez entrer votre adresse email')
      return
    }

    setLoading(true)
    try {
      const data = await authClient.forgotPassword(email)
      setSuccess(true)
      if (data.reset_token) {
        toast.success(`Mode dev — jeton : ${data.reset_token}`)
      } else {
        toast.success('Si un compte existe, un jeton de réinitialisation a été généré.')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-gray-50 px-4 py-10">
      <Card className="w-full max-w-md">
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Mot de passe oublié</h1>
          <p className="text-gray-600">
            Entrez votre adresse email pour recevoir un lien de réinitialisation.
          </p>
        </div>

        {success ? (
          <div className="text-center space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <p className="text-green-800 font-medium">Email envoyé avec succès !</p>
              <p className="text-sm text-green-600 mt-2">
                Un lien de réinitialisation a été envoyé à <strong>{email}</strong>
              </p>
            </div>
            <Link href="/">
              <Button variant="primary" className="w-full">
                Retour à la connexion
              </Button>
            </Link>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Adresse email"
              type="email"
              placeholder="votre@email.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value)
                setError('')
              }}
              required
              error={error}
            />

            <Button
              type="submit"
              disabled={loading}
              className="w-full"
              variant="primary"
            >
              {loading ? 'Envoi en cours...' : 'Envoyer le lien de réinitialisation'}
            </Button>
          </form>
        )}

        <div className="mt-6 text-center">
          <Link href="/" className="text-sm text-[#003366] hover:text-[#004080] font-medium">
            Retour à la connexion
          </Link>
        </div>
      </Card>
    </div>
  )
}
