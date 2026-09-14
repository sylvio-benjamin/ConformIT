'use client'

export default function LoadingSpinner({ message = 'Chargement...' }) {
  return (
    <div className="flex min-h-[50vh] w-full items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#003366] mx-auto"></div>
        <p className="mt-4 text-gray-600">{message}</p>
      </div>
    </div>
  )
}

