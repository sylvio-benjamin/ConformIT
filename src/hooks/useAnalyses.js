import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { analysesAPI } from "@/services/api";

/**
 * Hook personnalisé pour gérer les analyses depuis PostgreSQL
 */
export function useAnalyses() {
  const { user } = useAuth();
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user || !user.uid) {
      setLoading(false);
      return;
    }

    async function fetchAnalyses() {
      try {
        setLoading(true);
        setError(null);
        console.log("🔄 Récupération des analyses pour l'utilisateur:", user.uid);
        const data = await analysesAPI.list(user);
        console.log("✅ Analyses récupérées:", data);
        setAnalyses(data.analyses || []);
      } catch (err) {
        console.error("❌ Erreur lors du chargement des analyses:", err);
        console.error("Détails de l'erreur:", err.message, err.stack);
        setError(err.message);
        setAnalyses([]);
      } finally {
        setLoading(false);
      }
    }

    fetchAnalyses();
  }, [user]);

  const refresh = async () => {
    if (!user) return;
    try {
      const data = await analysesAPI.list(user);
      setAnalyses(data.analyses || []);
    } catch (err) {
      console.error("Erreur lors du rafraîchissement:", err);
      setError(err.message);
    }
  };

  const deleteAnalysis = async (slug) => {
    if (!user) return;
    try {
      await analysesAPI.delete(user, slug);
      setAnalyses(analyses.filter(a => a.slug !== slug));
    } catch (err) {
      console.error("Erreur lors de la suppression:", err);
      throw err;
    }
  };

  return { analyses, loading, error, refresh, deleteAnalysis };
}

/**
 * Hook pour une analyse spécifique
 */
export function useAnalysis(slug) {
  const { user } = useAuth();
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user || !slug) {
      setLoading(false);
      return;
    }

    async function fetchAnalysis() {
      try {
        setLoading(true);
        setError(null);
        const data = await analysesAPI.getBySlug(user, slug);
        setAnalysis(data);
      } catch (err) {
        console.error("Erreur lors du chargement de l'analyse:", err);
        setError(err.message);
        setAnalysis(null);
      } finally {
        setLoading(false);
      }
    }

    fetchAnalysis();
  }, [user, slug]);

  const update = async (updates) => {
    if (!user || !slug) return;
    try {
      await analysesAPI.update(user, slug, updates);
      const updated = await analysesAPI.getBySlug(user, slug);
      setAnalysis(updated);
    } catch (err) {
      console.error("Erreur lors de la mise à jour:", err);
      throw err;
    }
  };

  return { analysis, loading, error, update };
}

