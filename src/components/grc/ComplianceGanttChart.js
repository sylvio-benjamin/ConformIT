'use client'

import { useEffect, useRef } from 'react'

/**
 * Graphique de Gantt pour planifier et suivre les actions correctives
 */
export default function ComplianceGanttChart({ data = [] }) {
  const containerRef = useRef(null)

  useEffect(() => {
    // Ce composant utilise une approche simple avec des divs
    // Pour une version plus avancée, on pourrait utiliser une bibliothèque comme react-gantt-chart
  }, [data])

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Aucune action corrective à afficher
      </div>
    )
  }

  // Helper pour parser les dates ISO
  const parseISO = (dateString) => {
    if (!dateString) return null
    return new Date(dateString)
  }

  // Helper pour formater les dates
  const formatDate = (date) => {
    if (!date) return ''
    const d = new Date(date)
    return d.toLocaleDateString('fr-FR', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  // Calculer les dates min et max
  const allDates = data
    .flatMap(item => [
      item.created_at ? parseISO(item.created_at) : null,
      item.due_date ? parseISO(item.due_date) : null,
      item.completed_at ? parseISO(item.completed_at) : null
    ])
    .filter(Boolean)

  const minDate = allDates.length > 0 ? new Date(Math.min(...allDates.map(d => d.getTime()))) : new Date()
  const maxDate = allDates.length > 0 ? new Date(Math.max(...allDates.map(d => d.getTime()))) : new Date()

  const totalDays = Math.max(1, Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24)))

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'in_progress':
        return 'bg-blue-500'
      case 'planned':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-400'
    }
  }

  const getBarPosition = (item) => {
    if (!item.created_at) return { left: 0, width: 0 }
    
    const startDate = parseISO(item.created_at)
    const endDate = item.completed_at ? parseISO(item.completed_at) : (item.due_date ? parseISO(item.due_date) : new Date())
    
    const daysFromStart = Math.max(0, Math.ceil((startDate - minDate) / (1000 * 60 * 60 * 24)))
    const daysDuration = Math.max(1, Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)))
    
    const leftPercent = (daysFromStart / totalDays) * 100
    const widthPercent = (daysDuration / totalDays) * 100
    
    return { left: leftPercent, width: widthPercent }
  }

  return (
    <div className="w-full overflow-x-auto">
      <div className="min-w-full" ref={containerRef}>
        {/* Timeline header */}
        <div className="flex border-b border-gray-300 mb-4 pb-2">
          <div className="w-64 flex-shrink-0 font-semibold text-sm text-gray-700">Action</div>
          <div className="flex-1 relative">
            <div className="flex justify-between text-xs text-gray-500">
              <span>{formatDate(minDate)}</span>
              <span>{formatDate(maxDate)}</span>
            </div>
          </div>
        </div>

        {/* Gantt bars */}
        <div className="space-y-3">
          {data.map((item, index) => {
            const position = getBarPosition(item)
            return (
              <div key={item.id || index} className="flex items-center">
                <div className="w-64 flex-shrink-0 text-sm text-gray-700 truncate pr-4">
                  {item.title || `Action ${index + 1}`}
                </div>
                <div className="flex-1 relative h-8 bg-gray-100 rounded">
                  {position.width > 0 && (
                    <div
                      className={`absolute h-full ${getStatusColor(item.status)} rounded flex items-center px-2 text-white text-xs`}
                      style={{
                        left: `${position.left}%`,
                        width: `${Math.min(position.width, 100 - position.left)}%`,
                        minWidth: '20px'
                      }}
                      title={`${item.title} - ${item.status} - ${item.due_date ? formatDate(parseISO(item.due_date)) : 'No due date'}`}
                    >
                      <span className="truncate">{item.status}</span>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span>Terminé</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-500 rounded"></div>
            <span>En cours</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-yellow-500 rounded"></div>
            <span>Planifié</span>
          </div>
        </div>
      </div>
    </div>
  )
}
