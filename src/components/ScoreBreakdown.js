'use client'

export default function ScoreBreakdown({ breakdown }) {
  if (!breakdown || !breakdown.by_type) return null

  const types = Object.values(breakdown.by_type)
  const globalScore = breakdown.score_global ?? 0
  const level = breakdown.niveau_risque_label || breakdown.niveau_risque

  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Pourquoi ce score ?</h2>
        <p className="mt-1 text-sm text-gray-600">
          Score global {globalScore} / 100 → {level}. Chaque famille est notée séparément, puis pondérée.
        </p>
        {breakdown.formula && (
          <p className="mt-1 text-xs text-gray-500">
            S_r = min(100, B_r / Cap_r × 100) · S_global = Σ (S_r × W_r) / 100
          </p>
        )}
        {breakdown.extraction_incomplete && (
          <p className="mt-2 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            {breakdown.extraction_failed_count || 0} question(s) n’ont pas pu être lues
            (quota API dépassé ou erreur d’extraction). Elles ne comptent pas dans le score.
          </p>
        )}
      </div>
      <div className="space-y-3">
        {types.map((row) => (
          <div key={row.risk_type} className="rounded-lg border border-gray-200 bg-gray-50 p-4">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="font-semibold text-gray-900">{row.label}</p>
              <p className="text-sm text-gray-600">
                {row.score} / 100 · poids {row.weight} · contribution {row.contribution}
              </p>
            </div>
            {row.formula && (
              <p className="mt-1 text-xs text-gray-500">{row.formula}</p>
            )}
            {row.rules?.length ? (
              <ul className="mt-3 space-y-2">
                {row.rules.map((rule) => (
                  <li key={rule.rule_id} className="rounded-md bg-white px-3 py-2 text-sm">
                    <p className="font-medium text-gray-800">
                      {rule.rule_id} · {rule.title}
                    </p>
                    <p className="text-xs text-gray-500">
                      {rule.condition ? `${rule.condition} · ` : ''}
                      impact {rule.impact}/{rule.max_impact}
                      {rule.version ? ` · v${rule.version}` : ''}
                    </p>
                    {rule.fact && (
                      <p className="mt-1 text-xs text-gray-600">Fait : {rule.fact}</p>
                    )}
                    {rule.finding && rule.finding !== rule.fact && (
                      <p className="text-xs text-gray-500">{rule.finding}</p>
                    )}
                    {(rule.page || rule.snippet) && (
                      <p className="mt-1 text-xs text-gray-500">
                        {rule.page ? `Page ${rule.page}` : 'Extrait'}
                        {rule.snippet ? ` · « ${rule.snippet} »` : ''}
                      </p>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-xs text-gray-500">Aucune règle déclenchée pour cette famille.</p>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
