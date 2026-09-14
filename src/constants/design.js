/**
 * Constantes de design pour uniformiser l'application
 */

export const COLORS = {
  // Couleurs principales
  primary: '#003366',
  primaryDark: '#004080',
  primaryLight: '#0059b3',
  
  // Couleurs secondaires
  secondary: '#00A859',
  secondaryDark: '#008547',
  secondaryLight: '#00C966',
  
  // Couleurs d'accent
  accent: '#FF9F1C',
  accentDark: '#E68900',
  accentLight: '#FFB84D',
  
  // Couleurs de risque
  risk: {
    low: {
      bg: 'bg-green-100',
      text: 'text-green-700',
      border: 'border-green-300',
      hex: '#00C49F',
    },
    medium: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-700',
      border: 'border-yellow-300',
      hex: '#FFBB28',
    },
    high: {
      bg: 'bg-orange-100',
      text: 'text-orange-700',
      border: 'border-orange-300',
      hex: '#FF8042',
    },
    critical: {
      bg: 'bg-red-100',
      text: 'text-red-700',
      border: 'border-red-300',
      hex: '#FF0000',
    },
  },
  
  // Couleurs de score
  score: {
    green: {
      bg: 'bg-green-100',
      text: 'text-green-700',
      hex: '#00C49F',
    },
    yellow: {
      bg: 'bg-yellow-100',
      text: 'text-yellow-700',
      hex: '#FFBB28',
    },
    orange: {
      bg: 'bg-orange-100',
      text: 'text-orange-700',
      hex: '#FF8042',
    },
    red: {
      bg: 'bg-red-100',
      text: 'text-red-700',
      hex: '#FF0000',
    },
  },
  
  // Couleurs neutres
  gray: {
    50: '#F5F7FA',
    100: '#E4E7EB',
    200: '#CBD2D9',
    300: '#9AA5B1',
    400: '#7B8794',
    500: '#616E7C',
    600: '#52606D',
    700: '#3E4C59',
    800: '#323F4B',
    900: '#1F2933',
  },
}

export const SPACING = {
  xs: '0.25rem',    // 4px
  sm: '0.5rem',     // 8px
  md: '1rem',       // 16px
  lg: '1.5rem',     // 24px
  xl: '2rem',       // 32px
  '2xl': '3rem',    // 48px
  '3xl': '4rem',    // 64px
}

export const TYPOGRAPHY = {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['monospace'],
  },
  fontSize: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.125rem',   // 18px
    xl: '1.25rem',    // 20px
    '2xl': '1.5rem',  // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
}

export const BORDER_RADIUS = {
  sm: '0.25rem',   // 4px
  md: '0.5rem',    // 8px
  lg: '0.75rem',   // 12px
  xl: '1rem',      // 16px
  '2xl': '1.5rem', // 24px
  full: '9999px',
}

export const SHADOW = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
}

export const TRANSITION = {
  fast: '150ms ease-in-out',
  normal: '200ms ease-in-out',
  slow: '300ms ease-in-out',
}

export const BREAKPOINTS = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
}

// Classes Tailwind communes
export const COMMON_CLASSES = {
  // Layout
  container: 'max-w-7xl mx-auto px-4 sm:px-6 lg:px-8',
  pageContainer: 'min-h-screen bg-gray-50',
  mainContent: 'max-w-7xl mx-auto py-6 sm:px-6 lg:px-8',
  contentWrapper: 'px-4 py-6 sm:px-0',
  
  // Cards
  card: 'bg-white rounded-xl shadow-md p-6',
  cardHover: 'bg-white rounded-xl shadow-md p-6 hover:shadow-lg transition',
  
  // Buttons
  buttonPrimary: 'px-4 py-2 bg-[#003366] text-white rounded-lg hover:bg-[#004080] transition font-medium',
  buttonSecondary: 'px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition font-medium',
  buttonDanger: 'px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition font-medium',
  buttonSuccess: 'px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition font-medium',
  
  // Inputs
  input: 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent',
  select: 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent',
  textarea: 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#003366] focus:border-transparent resize-none',
  
  // Tables
  table: 'w-full',
  tableHeader: 'bg-gray-50',
  tableHeaderCell: 'px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider',
  tableBody: 'bg-white divide-y divide-gray-200',
  tableRow: 'hover:bg-gray-50',
  tableCell: 'px-6 py-4 whitespace-nowrap text-sm text-gray-900',
  
  // Badges
  badge: 'px-2 py-1 text-xs font-semibold rounded-full',
  badgePrimary: 'px-2 py-1 text-xs font-semibold rounded-full bg-[#003366] text-white',
  badgeSuccess: 'px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-700',
  badgeWarning: 'px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-700',
  badgeDanger: 'px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-700',
  
  // Loading
  loadingSpinner: 'animate-spin rounded-full h-12 w-12 border-b-2 border-[#003366]',
  
  // Modals
  modalOverlay: 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50',
  modalContent: 'bg-white rounded-xl shadow-xl p-6 w-full max-w-2xl',
}

