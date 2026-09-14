// /src/app/abonnement/page.jsx
'use client';

import { useState, useEffect } from 'react';
import { CheckCircle, CreditCard, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function AbonnementsPage() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const [status, setStatus] = useState('free');
  const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
      if (!user) return;
      setStatus(user.abonnement || 'basic');
      setIsLoading(false);
    }, [user]);
    

  const handleSubscribe = async (tier) => {
    try {
      setIsLoading(true);
      const res = await fetch('http://localhost:8000/stripe/create-checkout-session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: user.uid, entrepriseId: user.entreprise, plan: tier })
      });
      const { url } = await res.json();
      window.location.href = url;
    } catch (err) {
      alert('Erreur lors de la redirection vers Stripe');
      setIsLoading(false);
    }
  };

  if (loading || isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="animate-spin" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-3xl font-bold mb-6">🎟️ Choisissez votre abonnement</h1>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            { tier: 'free', name: 'Gratuit', price: '0€', features: ['3 analyses/mois', 'Export PDF uniquement'] },
            { tier: 'pro', name: 'Pro', price: '9€/mois', features: ['30 analyses/mois', 'Export Excel + PDF', 'Synthèse IA'] },
            { tier: 'premium', name: 'Premium', price: '29€/mois', features: ['Analyses illimitées', 'Historique complet', 'Toutes les fonctionnalités'] }
          ].map(({ tier, name, price, features }) => (
            <div key={tier} className={`rounded-xl shadow p-6 bg-white ${status === tier ? 'border-2 border-blue-500' : ''}`}>
              <h2 className="text-xl font-semibold mb-2">{name}</h2>
              <p className="text-2xl font-bold mb-4">{price}</p>
              <ul className="text-left mb-4">
                {features.map((f, i) => (
                  <li key={i} className="flex items-center gap-2 mb-1">
                    <CheckCircle className="text-green-500" size={16} /> {f}
                  </li>
                ))}
              </ul>
              {status === tier ? (
                <div className="text-green-600 font-semibold">✅ Actif</div>
              ) : (
                <button
                  onClick={() => handleSubscribe(tier)}
                  className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition"
                >
                  <CreditCard size={16} /> Choisir {name}
                </button>
              )}
            </div>
          ))}
        </div>

        <Link href="/employe" className="block mt-6 text-blue-500 hover:underline">
          ← Retour à l&apos;espace employé
        </Link>
      </div>
    </div>
  );
}
