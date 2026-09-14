import { useState, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { usersAPI } from "@/services/api";

/**
 * Hook personnalisé pour gérer le profil utilisateur depuis PostgreSQL
 */
export function useUserProfile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    async function fetchProfile() {
      try {
        setLoading(true);
        setError(null);
        
        // Créer ou récupérer l'utilisateur
        const data = await usersAPI.getCurrentUser(user).catch(async () => {
          // Si l'utilisateur n'existe pas, le créer
          return await usersAPI.createOrUpdateUser(user, user.email);
        });
        
        setProfile(data);
      } catch (err) {
        console.error("Erreur lors du chargement du profil:", err);
        setError(err.message);
        setProfile(null);
      } finally {
        setLoading(false);
      }
    }

    fetchProfile();
  }, [user]);

  const updateProfile = async (updates) => {
    if (!user) return;
    try {
      const updated = await usersAPI.updateProfile(user, updates);
      setProfile(updated);
      return updated;
    } catch (err) {
      console.error("Erreur lors de la mise à jour du profil:", err);
      throw err;
    }
  };

  return { profile, loading, error, updateProfile };
}

/**
 * Hook pour gérer les collaborateurs
 */
export function useCollaborators() {
  const { user } = useAuth();
  const { profile } = useUserProfile();
  const [collaborators, setCollaborators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user || !profile?.id) {
      setLoading(false);
      return;
    }

    async function fetchCollaborators() {
      try {
        setLoading(true);
        setError(null);
        const data = await usersAPI.getCollaborators(user, profile.id);
        setCollaborators(data.collaborators || []);
      } catch (err) {
        console.error("Erreur lors du chargement des collaborateurs:", err);
        setError(err.message);
        setCollaborators([]);
      } finally {
        setLoading(false);
      }
    }

    fetchCollaborators();
  }, [user, profile?.id]);

  const addCollaborator = async (email) => {
    if (!user || !profile?.id) return;
    try {
      const newCollaborator = await usersAPI.addCollaborator(user, profile.id, email);
      setCollaborators([...collaborators, newCollaborator]);
      return newCollaborator;
    } catch (err) {
      console.error("Erreur lors de l'ajout du collaborateur:", err);
      throw err;
    }
  };

  const removeCollaborator = async (collaboratorId) => {
    if (!user || !profile?.id) return;
    try {
      await usersAPI.removeCollaborator(user, profile.id, collaboratorId);
      setCollaborators(collaborators.filter(c => c.id !== collaboratorId));
    } catch (err) {
      console.error("Erreur lors de la suppression du collaborateur:", err);
      throw err;
    }
  };

  return { collaborators, loading, error, addCollaborator, removeCollaborator };
}

