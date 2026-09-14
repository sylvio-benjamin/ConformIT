'use client'

import Link from 'next/link'

export default function NavbarAdmin() {
  return (
    <nav className="bg-white shadow-md px-6 py-4 flex justify-between items-center relative">
 
      <div className="text-xl font-bold text-blue-600 z-10">Admin</div>


      <div className="absolute left-1/2 transform -translate-x-1/2 flex gap-6 text-gray-700">
        <Link href="/admin" className="hover:text-blue-600">Accueil</Link>
        <Link href="/admin/utilisateur" className="hover:text-blue-600">Liste</Link>
        <Link href="/admin/utilisateur/ajouter" className="hover:text-blue-600">Ajouter</Link>
        <Link href="/admin/utilisateur/modifier" className="hover:text-blue-600">Modifier</Link>
      </div>

    
      <div className="w-[72px]" /> 
    </nav>
  )
}
