CREATE DATABASE IF NOT EXISTS mydb;
USE mydb;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Proposal statuses:
--   AI Pipeline: Ingesting → Analyzing → Designing → Planning → Assembling → Complete → Failed
--   Business Workflow: Complete → Draft → DeliveryReview → PartnerReview → Approved → Published
--   Rejection: PartnerReview → Draft (back for revision)
CREATE TABLE IF NOT EXISTS proposals (
    id VARCHAR(50) PRIMARY KEY,
    client_name VARCHAR(255) NOT NULL,
    project_duration VARCHAR(100) NOT NULL,
    budget VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'Ingesting',
    submitted_by_role VARCHAR(50) NULL,        -- Role that last transitioned the proposal
    last_transitioned_at TIMESTAMP NULL,       -- When the last business transition happened
    generated_file_path VARCHAR(500) NULL,
    structured_json_ir LONGTEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge_assets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(100) NOT NULL, -- 'Asset' or 'Competency'
    capabilities TEXT NOT NULL,      -- Comma-separated list or JSON array of tags
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS proposal_steps (
    id INT AUTO_INCREMENT PRIMARY KEY,
    proposal_id VARCHAR(50) NOT NULL,
    step_name VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,     -- 'pending', 'running', 'completed', 'failed'
    log_message TEXT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (proposal_id) REFERENCES proposals(id) ON DELETE CASCADE
);

-- Insert default admin and business users if not exists
INSERT IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'password', 'admin');
INSERT IGNORE INTO users (id, username, password, role) VALUES (2, 'presales', 'password', 'presales');
INSERT IGNORE INTO users (id, username, password, role) VALUES (3, 'bidmanager', 'password', 'bidmanager');
INSERT IGNORE INTO users (id, username, password, role) VALUES (4, 'delivery', 'password', 'delivery');
INSERT IGNORE INTO users (id, username, password, role) VALUES (5, 'partner', 'password', 'partner');


-- Seed some default competencies and assets
INSERT IGNORE INTO knowledge_assets (name, description, category, capabilities) VALUES
('Enterprise Cloud Migration Toolkit', 'A framework containing reusable Ansible and Terraform templates for migrating enterprise Java/React apps to AWS/Azure.', 'Asset', 'AWS,Azure,Terraform,Ansible,Migration,Java,React'),
('Enterprise Data Governance Framework', 'Standard templates, policies, and schemas for metadata management, lineage tracking, and data cataloging.', 'Asset', 'Governance,Collibra,Data Catalog,Metadata,SQL'),
('DevOps Pipeline Accelerator', 'Pre-configured CI/CD pipelines using GitHub Actions and GitLab CI, with integrated security scans (Snyk, SonarQube).', 'Asset', 'DevOps,GitHub Actions,GitLab CI,Snyk,SonarQube,Docker,Kubernetes'),
('React/TypeScript Front-End Competency', 'Large pool of skilled front-end engineers specializing in React, TypeScript, State Management (Zustand/Redux), and Tailwind CSS.', 'Competency', 'React,TypeScript,Zustand,Tailwind CSS,Vite'),
('Python Data Engineering Competency', 'Team of data engineers experienced in PySpark, Pandas, Airflow, and building robust ETL pipelines.', 'Competency', 'Python,PySpark,Pandas,Airflow,ETL,Data Pipeline'),
('Cybersecurity Compliance Competency', 'Certified auditors and engineers specializing in ISO27001, SOC2, and data privacy compliance assessments.', 'Competency', 'ISO27001,SOC2,Cybersecurity,Compliance,Audit');

-- -------------------------------------------------------
-- MIGRATION: Add workflow tracking columns to existing proposals table
-- These are idempotent — safe to re-run on already-migrated databases
-- -------------------------------------------------------
-- Migration queries have been removed because MySQL does not support ADD COLUMN IF NOT EXISTS.
-- The columns are already included in the CREATE TABLE proposals statement.
