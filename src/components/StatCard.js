'use client'

/**
 * Carte de statistique uniforme pour les dashboards
 */
export default function StatCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  color = 'blue',
  onClick,
  className = ''
}) {
  const colorClasses = {
    blue: 'bg-blue-500 text-white',
    green: 'bg-green-500 text-white',
    orange: 'bg-orange-500 text-white',
    red: 'bg-red-500 text-white',
    purple: 'bg-purple-500 text-white',
    indigo: 'bg-indigo-500 text-white',
  }

  const cardColor = colorClasses[color] || colorClasses.blue
  const cursorClass = onClick ? 'cursor-pointer' : ''

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition ${cursorClass} ${className}`}
    >
      <div className="flex items-center justify-between mb-4">
        {Icon && (
          <div className={`${cardColor} p-3 rounded-lg`}>
            <Icon className="h-6 w-6" />
          </div>
        )}
      </div>
      <h3 className="text-2xl font-bold text-gray-900 mb-1">{value}</h3>
      <p className="text-sm font-medium text-gray-700 mb-1">{title}</p>
      {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
    </div>
  )
}

