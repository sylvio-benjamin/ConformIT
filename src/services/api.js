/**
 * Service API pour communiquer avec le backend PostgreSQL.
 * Remplace les appels Firebase directs pour les données.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Appel API authentifié via cookie de session (credentials: include).
 */
async function apiCall(endpoint, options = {}) {
  const { user, ...restOptions } = options;
  
  const url = `${API_BASE_URL}${endpoint}`;
  
  const config = {
    ...restOptions,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...restOptions.headers,
    },
  };
  
  if (restOptions.body && typeof restOptions.body === 'object') {
    config.body = JSON.stringify(restOptions.body);
  }
  
  const response = await fetch(url, config);

  if (!response.ok) {
    const errorText = await response.text();
    let error;
    try {
      error = JSON.parse(errorText);
    } catch {
      error = { detail: errorText || response.statusText };
    }
    const message = typeof error.detail === 'string' ? error.detail : `Erreur ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

// ==================== USERS API ====================

export const usersAPI = {
  /**
   * Récupère le profil utilisateur
   */
  async getCurrentUser(user) {
    return apiCall('/api/users/me', { user });
  },
  
  /**
   * Crée ou met à jour un utilisateur
   */
  async createOrUpdateUser(user, email) {
    return apiCall('/api/users/me', {
      method: 'POST',
      user,
      body: { email },
    });
  },
  
  /**
   * Met à jour le profil utilisateur
   */
  async updateProfile(user, updates) {
    return apiCall('/api/users/me', {
      method: 'PUT',
      user,
      body: updates,
    });
  },
  
  /**
   * Liste les collaborateurs
   */
  async getCollaborators(user, userId) {
    return apiCall(`/api/users/${userId}/collaborators`, { user });
  },
  
  /**
   * Ajoute un collaborateur
   */
  async addCollaborator(user, userId, email) {
    return apiCall(`/api/users/${userId}/collaborators`, {
      method: 'POST',
      user,
      body: { email },
    });
  },
  
  /**
   * Supprime un collaborateur
   */
  async removeCollaborator(user, userId, collaboratorId) {
    return apiCall(`/api/users/${userId}/collaborators/${collaboratorId}`, {
      method: 'DELETE',
      user,
    });
  },
};

// ==================== ANALYSES API ====================

export const analysesAPI = {
  /**
   * Liste les analyses d'un utilisateur
   */
  async list(user) {
    return apiCall('/api/analyses', { user });
  },
  
  /**
   * Récupère une analyse par slug
   */
  async getBySlug(user, slug) {
    return apiCall(`/api/analyses/${slug}`, { user });
  },
  
  /**
   * Crée une nouvelle analyse
   */
  async create(user, analysisData) {
    return apiCall('/api/analyses', {
      method: 'POST',
      user,
      body: analysisData,
    });
  },
  
  /**
   * Met à jour une analyse
   */
  async update(user, slug, updates) {
    return apiCall(`/api/analyses/${slug}`, {
      method: 'PUT',
      user,
      body: updates,
    });
  },
  
  /**
   * Supprime une analyse
   */
  async delete(user, slug) {
    return apiCall(`/api/analyses/${slug}`, {
      method: 'DELETE',
      user,
    });
  },
  
  /**
   * Liste les entreprises
   */
  async listCompanies(user) {
    return apiCall('/api/analyses/companies/list', { user });
  },

  async listJobs() {
    return apiCall('/api/v1/analysis-jobs');
  },

  async getJob(jobId) {
    return apiCall(`/api/v1/analysis-jobs/${jobId}`);
  },
};

// ==================== GRC API ====================

export const grcAPI = {
  risks: {
    async list(user, organizationId) {
      return apiCall(`/api/risks?organization_id=${organizationId}`, { user });
    },
    async get(user, organizationId, riskId) {
      return apiCall(`/api/risks/${riskId}?organization_id=${organizationId}`, { user });
    },
    async create(user, organizationId, riskData) {
      return apiCall('/api/risks', {
        method: 'POST',
        user,
        body: { ...riskData, organization_id: organizationId },
      });
    },
    async update(user, organizationId, riskId, updates) {
      return apiCall(`/api/risks/${riskId}`, {
        method: 'PUT',
        user,
        body: { ...updates, organization_id: organizationId },
      });
    },
    async delete(user, organizationId, riskId) {
      return apiCall(`/api/risks/${riskId}?organization_id=${organizationId}`, {
        method: 'DELETE',
        user,
      });
    },
  },
  
  controls: {
    async list(user, organizationId) {
      return apiCall(`/api/controls?organization_id=${organizationId}`, { user });
    },
    async get(user, organizationId, controlId) {
      return apiCall(`/api/controls/${controlId}?organization_id=${organizationId}`, { user });
    },
    async create(user, organizationId, controlData) {
      return apiCall('/api/controls', {
        method: 'POST',
        user,
        body: { ...controlData, organization_id: organizationId },
      });
    },
    async update(user, organizationId, controlId, updates) {
      return apiCall(`/api/controls/${controlId}`, {
        method: 'PUT',
        user,
        body: { ...updates, organization_id: organizationId },
      });
    },
    async delete(user, organizationId, controlId) {
      return apiCall(`/api/controls/${controlId}?organization_id=${organizationId}`, {
        method: 'DELETE',
        user,
      });
    },
  },
  
  incidents: {
    async list(user, organizationId) {
      return apiCall(`/api/incidents?organization_id=${organizationId}`, { user });
    },
    async get(user, organizationId, incidentId) {
      return apiCall(`/api/incidents/${incidentId}?organization_id=${organizationId}`, { user });
    },
    async create(user, organizationId, incidentData) {
      return apiCall('/api/incidents', {
        method: 'POST',
        user,
        body: { ...incidentData, organization_id: organizationId },
      });
    },
    async update(user, organizationId, incidentId, updates) {
      return apiCall(`/api/incidents/${incidentId}`, {
        method: 'PUT',
        user,
        body: { ...updates, organization_id: organizationId },
      });
    },
    async delete(user, organizationId, incidentId) {
      return apiCall(`/api/incidents/${incidentId}?organization_id=${organizationId}`, {
        method: 'DELETE',
        user,
      });
    },
  },
  
  kris: {
    async list(user, organizationId) {
      return apiCall(`/api/kris?organization_id=${organizationId}`, { user });
    },
    async get(user, organizationId, kriId) {
      return apiCall(`/api/kris/${kriId}?organization_id=${organizationId}`, { user });
    },
    async create(user, organizationId, kriData) {
      return apiCall('/api/kris', {
        method: 'POST',
        user,
        body: { ...kriData, organization_id: organizationId },
      });
    },
    async update(user, organizationId, kriId, updates) {
      return apiCall(`/api/kris/${kriId}`, {
        method: 'PUT',
        user,
        body: { ...updates, organization_id: organizationId },
      });
    },
    async delete(user, organizationId, kriId) {
      return apiCall(`/api/kris/${kriId}?organization_id=${organizationId}`, {
        method: 'DELETE',
        user,
      });
    },
  },
  
  reports: {
    async list(user, organizationId) {
      return apiCall('/api/reports', { user });
    },
    async create(user, organizationId, reportData) {
      return apiCall('/api/reports', {
        method: 'POST',
        user,
        body: reportData,
      });
    },
  },

  stats(user) {
    return apiCall('/api/grc/stats', { user });
  },

  compliance: {
    async get() {
      return apiCall('/api/v1/organizations/me/compliance');
    },
    async save(payload) {
      return apiCall('/api/v1/organizations/me/compliance', {
        method: 'PUT',
        body: payload,
      });
    },
  },

  profile: {
    async get() {
      return apiCall('/api/v1/organizations/me/profile');
    },
    async save(payload) {
      return apiCall('/api/v1/organizations/me/profile', {
        method: 'PUT',
        body: payload,
      });
    },
  },

  applicability: {
    async get() {
      return apiCall('/api/v1/organizations/me/applicability');
    },
    async evaluate() {
      return apiCall('/api/v1/organizations/me/applicability/evaluate', {
        method: 'POST',
      });
    },
    async standards() {
      return apiCall('/api/v1/organizations/me/applicable-standards');
    },
  },

  evidence: {
    async list(status) {
      const qs = status ? `?status=${encodeURIComponent(status)}` : '';
      return apiCall(`/api/v1/compliance-evidence${qs}`);
    },
    async review(id, status) {
      return apiCall(`/api/v1/compliance-evidence/${id}/review`, {
        method: 'POST',
        body: { status },
      });
    },
  },

  audits: {
    async list() {
      return apiCall('/api/v1/audits');
    },
    async create(payload) {
      return apiCall('/api/v1/audits', { method: 'POST', body: payload });
    },
    async get(id) {
      return apiCall(`/api/v1/audits/${id}`);
    },
    async addFinding(id, payload) {
      return apiCall(`/api/v1/audits/${id}/findings`, { method: 'POST', body: payload });
    },
    async importEvidence(id) {
      return apiCall(`/api/v1/audits/${id}/import-evidence`, { method: 'POST' });
    },
  },

  treatments: {
    async list(riskId) {
      const qs = riskId ? `?risk_id=${encodeURIComponent(riskId)}` : '';
      return apiCall(`/api/v1/risk-treatments${qs}`);
    },
    async create(payload) {
      return apiCall('/api/v1/risk-treatments', {
        method: 'POST',
        body: payload,
      });
    },
  },
};

export default {
  users: usersAPI,
  analyses: analysesAPI,
  grc: grcAPI,
};

