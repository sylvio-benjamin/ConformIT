'use client';

import { useState, useEffect } from 'react';
import { authClient } from '@/services/authClient';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    authClient.me().then((data) => {
      if (cancelled) return;
      setUser(data);
      setLoading(false);
    }).catch(() => {
      if (cancelled) return;
      setUser(null);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
  }, []);

  const logout = async () => {
    await authClient.logout();
    setUser(null);
  };

  return {
    user,
    loading,
    isAuthenticated: !!user,
    logout,
    setUser,
  };
}
