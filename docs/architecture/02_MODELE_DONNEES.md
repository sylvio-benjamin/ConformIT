# Modèle de Données - Plateforme SaaS de Gestion des Risques

## Vue d'ensemble

Modèle de données relationnel pour la plateforme de gestion des risques, conçu pour être scalable, performant et conforme aux normes ISO 31000, COSO ERM, etc.

---

## 1. Schéma de Base de Données

### 1.1 Entités Principales

#### **Users (Utilisateurs)**

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role_id UUID REFERENCES roles(id),
    organization_id UUID REFERENCES organizations(id),
    is_active BOOLEAN DEFAULT true,
    is_2fa_enabled BOOLEAN DEFAULT false,
    two_fa_secret VARCHAR(255),
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Organizations (Organisations)**

```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    siret VARCHAR(14),
    rcs VARCHAR(20),
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    industry VARCHAR(100),
    size VARCHAR(50), -- TPE, PME, ETI, Grande Entreprise
    plan VARCHAR(50), -- basic, pro, enterprise
    subscription_status VARCHAR(50), -- active, suspended, cancelled
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Roles (Rôles)**

```sql
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    is_system_role BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Permissions (Permissions)**

```sql
CREATE TABLE permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(100) NOT NULL, -- risk, control, incident, etc.
    action VARCHAR(50) NOT NULL, -- create, read, update, delete
    description TEXT
);
```

#### **RolePermissions (Rôles-Permissions)**

```sql
CREATE TABLE role_permissions (
    role_id UUID REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);
```

---

### 1.2 Module : Registre des Risques

#### **Risks (Risques)**

```sql
CREATE TABLE risks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL, -- RISK-001, RISK-002, etc.
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES risk_categories(id),
    owner_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'identified', -- identified, assessed, treated, accepted, closed
    parent_risk_id UUID REFERENCES risks(id), -- Pour hiérarchie
    priority VARCHAR(50), -- low, medium, high, critical
    tags TEXT[], -- Array de tags
    metadata JSONB, -- Métadonnées personnalisées
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);
```

#### **RiskCategories (Catégories de Risques)**

```sql
CREATE TABLE risk_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    parent_category_id UUID REFERENCES risk_categories(id),
    color VARCHAR(7), -- Code couleur hex
    icon VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **RiskDependencies (Dépendances de Risques)**

```sql
CREATE TABLE risk_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    depends_on_risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50), -- triggers, mitigates, exacerbates
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(risk_id, depends_on_risk_id)
);
```

---

### 1.3 Module : Évaluation & Scoring

#### **RiskAssessments (Évaluations de Risques)**

```sql
CREATE TABLE risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    assessed_by UUID REFERENCES users(id),
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    probability_level INTEGER, -- 1-5
    impact_level INTEGER, -- 1-5
    risk_level VARCHAR(50), -- Calculé: low, medium, high, critical
    risk_score INTEGER, -- Score normalisé 0-100
    methodology VARCHAR(50), -- qualitative, quantitative, semi-quantitative
    justification TEXT,
    confidence_level INTEGER, -- 1-5
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **RiskMatrices (Matrices de Risque)**

```sql
CREATE TABLE risk_matrices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    probability_levels INTEGER DEFAULT 5, -- Nombre de niveaux de probabilité
    impact_levels INTEGER DEFAULT 5, -- Nombre de niveaux d'impact
    matrix_config JSONB, -- Configuration de la matrice (seuils, couleurs)
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **RiskScores (Scores de Risques)**

```sql
CREATE TABLE risk_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    assessment_id UUID REFERENCES risk_assessments(id),
    score INTEGER NOT NULL, -- 0-100
    normalized_score DECIMAL(5,2), -- Score normalisé
    calculation_method VARCHAR(50),
    factors JSONB, -- Facteurs de calcul (probabilité, impact, etc.)
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 1.4 Module : Contrôles/Mesures de Maîtrise

#### **Controls (Contrôles)**

```sql
CREATE TABLE controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    control_type VARCHAR(50), -- preventive, detective, corrective
    control_category VARCHAR(50), -- technical, administrative, physical
    owner_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'planned', -- planned, in_progress, completed, verified
    effectiveness_rating INTEGER, -- 1-5
    last_test_date TIMESTAMP,
    next_test_date TIMESTAMP,
    documentation_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **RiskControls (Risques-Contrôles)**

```sql
CREATE TABLE risk_controls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    control_id UUID REFERENCES controls(id) ON DELETE CASCADE,
    effectiveness DECIMAL(5,2), -- Efficacité du contrôle sur le risque (0-100)
    is_primary BOOLEAN DEFAULT false, -- Contrôle principal ou secondaire
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(risk_id, control_id)
);
```

#### **ActionPlans (Plans d'Action)**

```sql
CREATE TABLE action_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_id UUID REFERENCES controls(id) ON DELETE CASCADE,
    risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES users(id),
    due_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'planned', -- planned, in_progress, completed, cancelled
    priority VARCHAR(50), -- low, medium, high, critical
    completion_percentage INTEGER DEFAULT 0,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **ControlTests (Tests de Contrôles)**

```sql
CREATE TABLE control_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    control_id UUID REFERENCES controls(id) ON DELETE CASCADE,
    test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tested_by UUID REFERENCES users(id),
    test_method VARCHAR(50), -- walkthrough, inquiry, observation, inspection
    test_result VARCHAR(50), -- passed, failed, partial
    findings TEXT,
    recommendations TEXT,
    next_test_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 1.5 Module : KRIs & Dashboards

#### **KRIs (Indicateurs Clés de Risque)**

```sql
CREATE TABLE kris (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    risk_id UUID REFERENCES risks(id),
    category_id UUID REFERENCES risk_categories(id),
    calculation_formula TEXT, -- Formule de calcul
    data_source VARCHAR(100), -- API, manual, import
    unit VARCHAR(50), -- percentage, count, currency, etc.
    frequency VARCHAR(50), -- daily, weekly, monthly, quarterly
    owner_id UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **KRIMetrics (Métriques KRI)**

```sql
CREATE TABLE kri_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kri_id UUID REFERENCES kris(id) ON DELETE CASCADE,
    measurement_date TIMESTAMP NOT NULL,
    value DECIMAL(15,2) NOT NULL,
    target_value DECIMAL(15,2),
    threshold_green DECIMAL(15,2),
    threshold_yellow DECIMAL(15,2),
    threshold_orange DECIMAL(15,2),
    threshold_red DECIMAL(15,2),
    status VARCHAR(50), -- green, yellow, orange, red
    data_source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **KRIAlerts (Alertes KRI)**

```sql
CREATE TABLE kri_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kri_id UUID REFERENCES kris(id) ON DELETE CASCADE,
    metric_id UUID REFERENCES kri_metrics(id),
    alert_type VARCHAR(50), -- threshold_exceeded, trend_change, anomaly
    severity VARCHAR(50), -- low, medium, high, critical
    message TEXT,
    status VARCHAR(50) DEFAULT 'active', -- active, acknowledged, resolved
    acknowledged_by UUID REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **Dashboards (Tableaux de Bord)**

```sql
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    layout JSONB, -- Configuration du layout
    is_shared BOOLEAN DEFAULT false,
    shared_with UUID[], -- Array d'user IDs
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **DashboardWidgets (Widgets de Tableau de Bord)**

```sql
CREATE TABLE dashboard_widgets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID REFERENCES dashboards(id) ON DELETE CASCADE,
    widget_type VARCHAR(50), -- chart, table, kpi, risk_matrix
    widget_config JSONB, -- Configuration du widget
    position_x INTEGER,
    position_y INTEGER,
    width INTEGER,
    height INTEGER,
    data_source VARCHAR(100), -- risk, control, incident, kri
    filters JSONB, -- Filtres appliqués
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 1.6 Module : Incident/Événement Management

#### **Incidents (Incidents)**

```sql
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    incident_type VARCHAR(50), -- security, operational, financial, etc.
    severity VARCHAR(50), -- low, medium, high, critical
    status VARCHAR(50) DEFAULT 'reported', -- reported, investigating, resolved, closed
    reported_by UUID REFERENCES users(id),
    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    impact_description TEXT,
    root_cause_analysis_id UUID REFERENCES root_cause_analyses(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **IncidentRisks (Incidents-Risques)**

```sql
CREATE TABLE incident_risks (
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    risk_id UUID REFERENCES risks(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50), -- triggered_by, mitigated_by, related_to
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (incident_id, risk_id)
);
```

#### **RootCauseAnalyses (Analyses de Cause Racine)**

```sql
CREATE TABLE root_cause_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    methodology VARCHAR(50), -- 5_why, ishikawa, fault_tree
    analysis TEXT,
    root_causes TEXT[], -- Array de causes racines
    contributing_factors TEXT[],
    analyzed_by UUID REFERENCES users(id),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **CorrectiveActions (Actions Correctives)**

```sql
CREATE TABLE corrective_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES users(id),
    due_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'planned',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **PreventiveActions (Actions Préventives)**

```sql
CREATE TABLE preventive_actions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    risk_id UUID REFERENCES risks(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES users(id),
    due_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'planned',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 1.7 Module : Conformité & Normes GRC

#### **ComplianceFrameworks (Cadres de Conformité)**

```sql
CREATE TABLE compliance_frameworks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL, -- ISO 31000, ISO 27005, COSO ERM, etc.
    code VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    version VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **ComplianceRequirements (Exigences de Conformité)**

```sql
CREATE TABLE compliance_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id UUID REFERENCES compliance_frameworks(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    requirement_type VARCHAR(50), -- mandatory, recommended, optional
    parent_requirement_id UUID REFERENCES compliance_requirements(id),
    section VARCHAR(100),
    subsection VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(framework_id, code)
);
```

#### **ComplianceAssessments (Évaluations de Conformité)**

```sql
CREATE TABLE compliance_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    framework_id UUID REFERENCES compliance_frameworks(id),
    requirement_id UUID REFERENCES compliance_requirements(id),
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    compliance_status VARCHAR(50), -- compliant, non_compliant, partially_compliant, not_applicable
    evidence TEXT,
    assessed_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **ComplianceGaps (Écarts de Conformité)**

```sql
CREATE TABLE compliance_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES compliance_assessments(id) ON DELETE CASCADE,
    gap_description TEXT NOT NULL,
    severity VARCHAR(50), -- low, medium, high, critical
    remediation_plan_id UUID REFERENCES compliance_remediations(id),
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, closed
    closed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **ComplianceRemediations (Plans de Remédiation)**

```sql
CREATE TABLE compliance_remediations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gap_id UUID REFERENCES compliance_gaps(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES users(id),
    due_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'planned',
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **ComplianceAudits (Audits de Conformité)**

```sql
CREATE TABLE compliance_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    framework_id UUID REFERENCES compliance_frameworks(id),
    audit_type VARCHAR(50), -- internal, external, self_assessment
    audit_date TIMESTAMP,
    auditor_name VARCHAR(255),
    audit_scope TEXT,
    findings TEXT,
    recommendations TEXT,
    audit_report_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 1.8 Module : Intégrations Externes

#### **ExternalIntegrations (Intégrations Externes)**

```sql
CREATE TABLE external_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    integration_type VARCHAR(50), -- infogreffe, insee, dun_bradstreet, powerbi
    name VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, error
    config JSONB, -- Configuration (API keys, endpoints, etc.)
    last_sync_at TIMESTAMP,
    sync_frequency VARCHAR(50), -- daily, weekly, monthly, manual
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **APICredentials (Identifiants API)**

```sql
CREATE TABLE api_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID REFERENCES external_integrations(id) ON DELETE CASCADE,
    credential_type VARCHAR(50), -- api_key, oauth_token, username_password
    credential_name VARCHAR(255),
    encrypted_value TEXT, -- Valeur chiffrée
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **DataSyncs (Synchronisations de Données)**

```sql
CREATE TABLE data_syncs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    integration_id UUID REFERENCES external_integrations(id) ON DELETE CASCADE,
    sync_type VARCHAR(50), -- full, incremental
    status VARCHAR(50), -- pending, running, completed, failed
    records_synced INTEGER,
    records_failed INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 1.9 Module : Rapports

#### **Reports (Rapports)**

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    report_type VARCHAR(50), -- risk_report, compliance_report, incident_report, etc.
    title VARCHAR(255) NOT NULL,
    template_id UUID REFERENCES report_templates(id),
    parameters JSONB, -- Paramètres du rapport (filtres, période, etc.)
    status VARCHAR(50) DEFAULT 'draft', -- draft, generating, completed, failed
    file_url TEXT,
    file_format VARCHAR(50), -- pdf, excel, word, powerpoint
    generated_by UUID REFERENCES users(id),
    generated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **ReportTemplates (Modèles de Rapports)**

```sql
CREATE TABLE report_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50),
    template_config JSONB, -- Configuration du modèle (sections, styles, etc.)
    is_system_template BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **ReportSchedules (Planifications de Rapports)**

```sql
CREATE TABLE report_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_template_id UUID REFERENCES report_templates(id) ON DELETE CASCADE,
    schedule_type VARCHAR(50), -- daily, weekly, monthly, quarterly, yearly
    schedule_config JSONB, -- Configuration de la planification (jour, heure, etc.)
    recipients UUID[], -- Array d'user IDs
    email_subject VARCHAR(255),
    email_body TEXT,
    is_active BOOLEAN DEFAULT true,
    next_run_at TIMESTAMP,
    last_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 1.10 Module : Sécurité & Audit

#### **AuditLogs (Logs d'Audit)**

```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL, -- create, update, delete, read
    resource_type VARCHAR(50) NOT NULL, -- risk, control, incident, etc.
    resource_id UUID,
    resource_name VARCHAR(255),
    changes JSONB, -- Changements effectués (avant/après)
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **SecurityPolicies (Politiques de Sécurité)**

```sql
CREATE TABLE security_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    policy_type VARCHAR(50), -- password, session, 2fa, encryption
    policy_config JSONB, -- Configuration de la politique
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Relations entre Entités

### 2.1 Relations Principales

```
Organizations
  ├── Users (1:N)
  ├── Risks (1:N)
  ├── Controls (1:N)
  ├── Incidents (1:N)
  ├── KRIs (1:N)
  ├── Dashboards (1:N)
  ├── ComplianceAssessments (1:N)
  └── ExternalIntegrations (1:N)

Risks
  ├── RiskAssessments (1:N)
  ├── RiskControls (N:M)
  ├── Controls (N:M via RiskControls)
  ├── IncidentRisks (N:M)
  ├── Incidents (N:M via IncidentRisks)
  ├── RiskDependencies (N:M)
  └── KRIs (1:N)

Controls
  ├── RiskControls (N:M)
  ├── Risks (N:M via RiskControls)
  ├── ActionPlans (1:N)
  └── ControlTests (1:N)

Incidents
  ├── IncidentRisks (N:M)
  ├── Risks (N:M via IncidentRisks)
  ├── RootCauseAnalyses (1:1)
  ├── CorrectiveActions (1:N)
  └── PreventiveActions (1:N)

ComplianceFrameworks
  └── ComplianceRequirements (1:N)

ComplianceRequirements
  └── ComplianceAssessments (1:N)

Users
  ├── Roles (N:1)
  └── Permissions (N:M via RolePermissions)
```

---

## 3. Index et Performances

### 3.1 Index Principaux

```sql
-- Index sur les clés étrangères
CREATE INDEX idx_risks_organization_id ON risks(organization_id);
CREATE INDEX idx_risks_category_id ON risks(category_id);
CREATE INDEX idx_risks_owner_id ON risks(owner_id);
CREATE INDEX idx_risks_status ON risks(status);
CREATE INDEX idx_risks_created_at ON risks(created_at);

CREATE INDEX idx_risk_assessments_risk_id ON risk_assessments(risk_id);
CREATE INDEX idx_risk_assessments_assessed_by ON risk_assessments(assessed_by);
CREATE INDEX idx_risk_assessments_assessment_date ON risk_assessments(assessment_date);

CREATE INDEX idx_controls_organization_id ON controls(organization_id);
CREATE INDEX idx_controls_owner_id ON controls(owner_id);
CREATE INDEX idx_controls_status ON controls(status);

CREATE INDEX idx_incidents_organization_id ON incidents(organization_id);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_reported_at ON incidents(reported_at);

CREATE INDEX idx_kris_organization_id ON kris(organization_id);
CREATE INDEX idx_kri_metrics_kri_id ON kri_metrics(kri_id);
CREATE INDEX idx_kri_metrics_measurement_date ON kri_metrics(measurement_date);

CREATE INDEX idx_audit_logs_organization_id ON audit_logs(organization_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);

-- Index pour les recherches full-text
CREATE INDEX idx_risks_title_gin ON risks USING GIN(to_tsvector('french', title));
CREATE INDEX idx_risks_description_gin ON risks USING GIN(to_tsvector('french', description));
```

---

## 4. Contraintes et Validations

### 4.1 Contraintes de Données

```sql
-- Contraintes de validation
ALTER TABLE risks ADD CONSTRAINT chk_risk_status 
    CHECK (status IN ('identified', 'assessed', 'treated', 'accepted', 'closed'));

ALTER TABLE risks ADD CONSTRAINT chk_risk_priority 
    CHECK (priority IN ('low', 'medium', 'high', 'critical'));

ALTER TABLE risk_assessments ADD CONSTRAINT chk_probability_level 
    CHECK (probability_level >= 1 AND probability_level <= 5);

ALTER TABLE risk_assessments ADD CONSTRAINT chk_impact_level 
    CHECK (impact_level >= 1 AND impact_level <= 5);

ALTER TABLE risk_assessments ADD CONSTRAINT chk_risk_level 
    CHECK (risk_level IN ('low', 'medium', 'high', 'critical'));

ALTER TABLE controls ADD CONSTRAINT chk_control_status 
    CHECK (status IN ('planned', 'in_progress', 'completed', 'verified'));

ALTER TABLE incidents ADD CONSTRAINT chk_incident_severity 
    CHECK (severity IN ('low', 'medium', 'high', 'critical'));

ALTER TABLE incidents ADD CONSTRAINT chk_incident_status 
    CHECK (status IN ('reported', 'investigating', 'resolved', 'closed'));
```

---

## 5. Migration et Évolution

### 5.1 Stratégie de Migration

- Utiliser des migrations versionnées (Alembic pour Python/FastAPI)
- Créer des scripts de migration pour chaque version
- Tester les migrations sur des données de test avant production
- Prévoir des rollbacks en cas de problème

### 5.2 Évolution du Schéma

- Ajouter des colonnes nullable pour la compatibilité ascendante
- Créer des vues pour masquer les changements de schéma
- Utiliser des migrations progressives (ajout → migration → suppression)

---

## 6. Sécurité des Données

### 6.1 Chiffrement

- Chiffrer les données sensibles au repos (AES-256)
- Chiffrer les données en transit (TLS/SSL)
- Chiffrer les identifiants API stockés
- Utiliser des secrets managés (AWS Secrets Manager, Azure Key Vault)

### 6.2 Accès aux Données

- Utiliser des vues pour limiter l'accès aux données
- Implémenter Row Level Security (RLS) pour l'isolation des organisations
- Utiliser des rôles de base de données pour les permissions
- Auditer tous les accès aux données sensibles

---

## 7. Backup et Restauration

### 7.1 Stratégie de Backup

- Sauvegardes quotidiennes complètes
- Sauvegardes incrémentielles toutes les heures
- Conservation des sauvegardes pendant 30 jours
- Sauvegardes géo-répliquées pour la résilience

### 7.2 Restauration

- Tests de restauration mensuels
- Procédures documentées pour la restauration
- Temps de restauration objectif (RTO) : 4 heures
- Point de restauration objectif (RPO) : 1 heure
