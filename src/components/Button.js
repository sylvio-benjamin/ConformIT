'use client'

import { isValidElement } from 'react'

/**
 * Bouton uniforme avec différentes variantes
 */
export default function Button({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  type = 'button',
  className = '',
  icon: Icon,
  ...props
}) {
  const variantClasses = {
    primary: 'bg-[#003366] text-white hover:bg-[#004080]',
    secondary: 'bg-gray-100 text-gray-700 hover:bg-gray-200',
    danger: 'bg-red-100 text-red-700 hover:bg-red-200',
    success: 'bg-green-100 text-green-700 hover:bg-green-200',
    outline: 'border border-[#003366] text-[#003366] hover:bg-[#003366] hover:text-white',
  }

  const sizeClasses = {
    sm: 'px-3 py-1 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  }

  const baseClasses = 'rounded-lg transition font-medium focus:outline-none focus:ring-2 focus:ring-[#003366] focus:ring-offset-2'
  const variantClass = variantClasses[variant] || variantClasses.primary
  const sizeClass = sizeClasses[size] || sizeClasses.md
  const disabledClass = disabled ? 'opacity-50 cursor-not-allowed' : ''

  // Rendre l'icône selon son type
  const renderIcon = () => {
    if (!Icon) return null
    
    // Si c'est un élément React valide (JSX), le rendre directement
    if (isValidElement(Icon)) {
      return Icon
    }
    
    // Si c'est une fonction/composant, le rendre comme composant
    if (typeof Icon === 'function') {
      return <Icon className="h-5 w-5" />
    }
    
    // Sinon, ne rien rendre (cas non supporté)
    return null
  }

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClass} ${sizeClass} ${disabledClass} ${className} flex items-center gap-2`}
      {...props}
    >
      {renderIcon()}
      {children}
    </button>
  )
}
