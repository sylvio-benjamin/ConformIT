'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authClient } from '@/services/authClient';

const PROTECTED_PREFIXES = [
  '/employe', '/admin', '/grc', '/historique',
  '/vue', '/analyses', '/risques', '/controles', '/conformite', '/rapports', '/compte',
];

export default function AuthProvider({ children }) {
  const [loadingAuth, setLoadingAuth] = useState(true);
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;

    authClient.me().then((user) => {
      if (cancelled) return;
      if (!user) {
        const path = window.location.pathname;
        if (PROTECTED_PREFIXES.some((route) => path.startsWith(route))) {
          router.push('/');
        }
      }
      setLoadingAuth(false);
    }).catch(() => {
      if (!cancelled) setLoadingAuth(false);
    });

    return () => {
      cancelled = true;
    };
  }, [router]);

  if (loadingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Chargement de l&apos;authentification...</p>
      </div>
    );
  }

  return <>{children}</>;
}
