-- ============================================================================
-- PostgreSQL Initialization Script for DeepAgents Control Platform
-- ============================================================================
--
-- This script runs automatically when the PostgreSQL container is first created
-- Use this for:
-- - Creating additional databases
-- - Setting up extensions
-- - Configuring database-specific settings
-- - Creating initial users (if needed)
--
-- ============================================================================

-- Enable required extensions
-- pg_stat_statements: Query performance monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- uuid-ossp: UUID generation functions (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- pgcrypto: Cryptographic functions (if needed)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Grant necessary permissions to the application user
-- (POSTGRES_USER from environment variables)
GRANT ALL PRIVILEGES ON DATABASE deepagents_prod TO deepagents;

-- Log initialization
SELECT 'DeepAgents Control Platform database initialized successfully' AS status;
