'use client'

import { useEffect, useRef } from 'react'

/**
 * Composant Speedometer (Jauge) pour afficher le score global de conformité (0-100%)
 * Utilise Canvas pour dessiner une jauge semi-circulaire
 */
export default function ComplianceSpeedometer({ score = 0, size = 200, strokeWidth = 20 }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    const centerX = size / 2
    const centerY = size / 2
    const radius = (size - strokeWidth) / 2 - 10
    const startAngle = Math.PI // 180 degrés (gauche)
    const endAngle = 0 // 0 degrés (droite)

    // Clear canvas
    ctx.clearRect(0, 0, size, size / 2 + strokeWidth)

    // Dessiner l'arc de fond (gris)
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, startAngle, endAngle, false)
    ctx.lineWidth = strokeWidth
    ctx.strokeStyle = '#E5E7EB'
    ctx.lineCap = 'round'
    ctx.stroke()

    // Calculer l'angle basé sur le score (0-100%)
    const scoreAngle = startAngle - (score / 100) * (startAngle - endAngle)

    // Déterminer la couleur en fonction du score
    let color = '#EF4444' // Rouge (< 50)
    if (score >= 80) {
      color = '#10B981' // Vert (>= 80)
    } else if (score >= 50) {
      color = '#F59E0B' // Orange (50-79)
    }

    // Dessiner l'arc de score
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, startAngle, scoreAngle, false)
    ctx.lineWidth = strokeWidth
    ctx.strokeStyle = color
    ctx.lineCap = 'round'
    ctx.stroke()

    // Dessiner le texte du score
    ctx.fillStyle = '#1F2937'
    ctx.font = `bold ${size / 5}px Arial`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    ctx.fillText(`${Math.round(score)}%`, centerX, centerY - 10)

    // Dessiner le label
    ctx.fillStyle = '#6B7280'
    ctx.font = `${size / 10}px Arial`
    ctx.fillText('Score global', centerX, centerY + 20)
  }, [score, size, strokeWidth])

  return (
    <div className="flex flex-col items-center">
      <canvas
        ref={canvasRef}
        width={size}
        height={size / 2 + strokeWidth + 30}
        className="max-w-full h-auto"
      />
    </div>
  )
}

