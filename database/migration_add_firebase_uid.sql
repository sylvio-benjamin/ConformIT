-- Migration: Ajouter firebase_uid et autres colonnes au modèle User
-- Date: 2024

-- Ajouter firebase_uid à la table users
ALTER TABLE users ADD COLUMN IF NOT EXISTS firebase_uid VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_firebase_uid ON users(firebase_uid) WHERE firebase_uid IS NOT NULL;

-- Ajouter les autres colonnes manquantes
ALTER TABLE users ADD COLUMN IF NOT EXISTS nom VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS prenom VARCHAR(100);
ALTER TABLE users ADD COLUMN IF NOT EXISTS entreprise VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS telephone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS abonnement VARCHAR(50) DEFAULT 'basic';
ALTER TABLE users ADD COLUMN IF NOT EXISTS preferences JSONB;

-- Rendre password_hash nullable car l'authentification est gérée par Firebase
ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;

-- Ajouter les tables pour les analyses si elles n'existent pas
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(255) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    employee_id UUID REFERENCES users(id) NOT NULL,
    company_id VARCHAR(255) REFERENCES companies(id),
    company_name VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    siret VARCHAR(14),
    rcs VARCHAR(20),
    document_type VARCHAR(100),
    risk_level VARCHAR(50),
    precision NUMERIC(5, 2),
    total_score INTEGER,
    quality VARCHAR(50),
    risk_color VARCHAR(50),
    status VARCHAR(50) DEFAULT 'Terminée',
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_analyses_slug ON analyses(slug);
CREATE INDEX IF NOT EXISTS idx_analyses_employee_id ON analyses(employee_id);
CREATE INDEX IF NOT EXISTS idx_analyses_organization_id ON analyses(organization_id);

CREATE TABLE IF NOT EXISTS companies (
    id VARCHAR(255) PRIMARY KEY,
    slug VARCHAR(255) UNIQUE NOT NULL,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    employee_id UUID REFERENCES users(id) NOT NULL,
    company_id VARCHAR(50),
    name VARCHAR(255) NOT NULL,
    rcs VARCHAR(20),
    company_type VARCHAR(100),
    risk VARCHAR(50),
    quality VARCHAR(50),
    total_score INTEGER,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_slug ON companies(slug);
CREATE INDEX IF NOT EXISTS idx_companies_employee_id ON companies(employee_id);
CREATE INDEX IF NOT EXISTS idx_companies_organization_id ON companies(organization_id);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES analyses(id) ON DELETE CASCADE,
    organization_id UUID REFERENCES organizations(id) ON DELETE CASCADE NOT NULL,
    employee_id UUID REFERENCES users(id) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    status VARCHAR(50) DEFAULT 'finalise',
    date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_analysis_id ON documents(analysis_id);
CREATE INDEX IF NOT EXISTS idx_documents_employee_id ON documents(employee_id);
CREATE INDEX IF NOT EXISTS idx_documents_organization_id ON documents(organization_id);

CREATE TABLE IF NOT EXISTS counters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_counters_key ON counters(key);

CREATE TABLE IF NOT EXISTS collaborators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    email VARCHAR(255) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_collaborators_user_id ON collaborators(user_id);

