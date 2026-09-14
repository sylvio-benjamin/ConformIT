'use client';

import { useQuota } from '@/hooks/useQuota';
import { AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';

/**
 * Composant affichant la barre de progression du quota d'analyses
 */
export default function QuotaProgress() {
  const { quota, loading } = useQuota();

  if (loading || !quota) {
    return (
      <div className="bg-white rounded-lg shadow p-4 animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
        <div className="h-2 bg-gray-200 rounded"></div>
      </div>
    );
  }

  // Plan illimité
  if (quota.unlimited) {
    return (
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg shadow p-4 border border-green-200">
        <div className="flex items-center gap-2 mb-2">
          <CheckCircle className="text-green-600" size={20} />
          <span className="font-semibold text-green-800">Plan Enterprise</span>
        </div>
        <p className="text-sm text-green-700">Analyses illimitées - Aucune limite</p>
      </div>
    );
  }

  const { count, limit, plan } = quota;
  const percentage = Math.min((count / limit) * 100, 100);
  const remaining = Math.max(limit - count, 0);
  const isWarning = percentage >= 80;
  const isCritical = percentage >= 100;

  // Calculer les jours jusqu'à la réinitialisation
  let daysUntilReset = null;
  if (quota.reset_date) {
    const resetDate = new Date(quota.reset_date);
    const now = new Date();
    const diffTime = resetDate - now;
    daysUntilReset = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  }

  return (
    <div className={`bg-white rounded-lg shadow p-4 border ${
      isCritical ? 'border-red-300' : isWarning ? 'border-yellow-300' : 'border-gray-200'
    }`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isCritical ? (
            <AlertCircle className="text-red-600" size={20} />
          ) : isWarning ? (
            <TrendingUp className="text-yellow-600" size={20} />
          ) : (
            <CheckCircle className="text-green-600" size={20} />
          )}
          <span className="font-semibold text-gray-800">
            Plan {plan.charAt(0).toUpperCase() + plan.slice(1)}
          </span>
        </div>
        <span className={`text-sm font-medium ${
          isCritical ? 'text-red-600' : isWarning ? 'text-yellow-600' : 'text-gray-600'
        }`}>
          {count} / {limit}
        </span>
      </div>

      {/* Barre de progression */}
      <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
        <div
          className={`h-3 rounded-full transition-all duration-300 ${
            isCritical
              ? 'bg-red-500'
              : isWarning
              ? 'bg-yellow-500'
              : 'bg-green-500'
          }`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>

      {/* Messages et actions */}
      {isCritical ? (
        <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
          <p className="text-sm text-red-800 font-medium mb-2">
            ⚠️ Limite d'analyses atteinte
          </p>
          <p className="text-xs text-red-700 mb-3">
            Vous avez utilisé toutes vos analyses pour ce mois.
            {daysUntilReset && ` Réinitialisation dans ${daysUntilReset} jour(s).`}
          </p>
          <p className="text-xs text-red-700">La facturation n’est pas activée sur cet environnement.</p>
        </div>
      ) : isWarning ? (
        <div className="mt-3 p-3 bg-yellow-50 rounded-lg border border-yellow-200">
          <p className="text-sm text-yellow-800 font-medium mb-1">
            ⚠️ Vous approchez de votre limite
          </p>
          <p className="text-xs text-yellow-700">
            Il vous reste {remaining} analyse{remaining > 1 ? 's' : ''} ce mois.
            {daysUntilReset && ` Réinitialisation dans ${daysUntilReset} jour(s).`}
          </p>
          {remaining <= 2 && (
            <p className="mt-2 text-xs text-yellow-700">La facturation n’est pas activée sur cet environnement.</p>
          )}
        </div>
      ) : (
        <p className="text-xs text-gray-600 mt-2">
          {remaining} analyse{remaining > 1 ? 's' : ''} restante{remaining > 1 ? 's' : ''} ce mois
          {daysUntilReset && ` • Réinitialisation dans ${daysUntilReset} jour(s)`}
        </p>
      )}
    </div>
  );
}

