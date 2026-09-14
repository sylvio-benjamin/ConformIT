'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function EmployeLayout({ children }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (loading) return;
    if (!user) {
      router.replace('/');
      return;
    }
    if (user.admin) {
      router.replace('/admin');
    }
  }, [user, loading, router]);

  if (loading) return <div>Chargement...</div>;
  return <>{children}</>;
} 