/** @type {import('next').NextConfig} */
const nextConfig = {
  async redirects() {
    return [
      { source: '/employe', destination: '/analyses', permanent: false },
      { source: '/historique', destination: '/analyses', permanent: false },
      { source: '/employe/dashboard', destination: '/vue', permanent: false },
      { source: '/employe/tableau-et-graph', destination: '/analyses', permanent: false },
      { source: '/employe/parametres', destination: '/compte', permanent: false },
      { source: '/employe/profile', destination: '/compte', permanent: false },
      { source: '/employe/attente', destination: '/analyses/attente', permanent: false },
      { source: '/abonnement', destination: '/compte', permanent: false },
      { source: '/abonnement/success', destination: '/compte', permanent: false },
      { source: '/abonnement/cancelled', destination: '/compte', permanent: false },
      { source: '/grc', destination: '/vue', permanent: false },
      { source: '/grc/visualizations', destination: '/vue', permanent: false },
      { source: '/grc/risks', destination: '/risques', permanent: false },
      { source: '/grc/controls', destination: '/controles', permanent: false },
      { source: '/grc/compliance', destination: '/conformite', permanent: false },
      { source: '/grc/reports', destination: '/rapports', permanent: false },
      { source: '/grc/integrations', destination: '/vue', permanent: false },
      { source: '/gdpr', destination: '/politique-confidentialite', permanent: false },
    ]
  },
}

export default nextConfig
