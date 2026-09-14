'use client';

import { useState, useEffect } from 'react';
import { useAuth } from './useAuth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export function useQuota() {
  const { user } = useAuth();
  const [quota, setQuota] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchQuota = async () => {
    if (!user) {
      setLoading(false);
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/quota/me`, {
        credentials: 'include',
      });
      if (!response.ok) {
        throw new Error('Erreur lors de la récupération du quota');
      }
      const data = await response.json();
      setQuota(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      setQuota({
        count: 0,
        limit: 5,
        plan: 'basic',
        unlimited: false,
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuota();
  }, [user]);

  return { quota, loading, error, refetch: fetchQuota };
}

export function usePlan() {
  const { quota, loading, error, refetch } = useQuota();
  return { plan: quota, loading, error, refetch };
}
