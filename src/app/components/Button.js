import { Plus } from 'lucide-react'

export default function BoutonAjout() {
  return (
    <div className="flex justify-center mt-6">
      <button
        type="button"
        className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center hover:bg-green-600 transition"
      >
        <Plus size={20} className="text-white" />
      </button>
    </div>
  )
}
