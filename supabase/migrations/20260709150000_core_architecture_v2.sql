-- ==============================================================================
-- Migration: 01 - Core Architecture V2 (Enterprise Edition)
-- Description: Criação das tabelas centrais do AI Decision Engine
-- (ai_agents, integrations, business_rules).
-- Nota: A tabela "clients" já existente permanece inalterada para garantir 
-- compatibilidade retroativa durante a transição. RLS desabilitado nesta fase.
-- ==============================================================================

-- Habilita pgcrypto para gen_random_uuid() (Padrão Enterprise Supabase)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ==============================================================================
-- 1. Table: ai_agents
-- Finalidade: Representa os "AI Employees" alocados por uma empresa.
-- Substitui a necessidade de manter system_prompt rígido na tabela clients.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS ai_agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    name TEXT NOT NULL CHECK (char_length(trim(name)) > 0),
    role TEXT NOT NULL,
    system_prompt TEXT NOT NULL CHECK (char_length(trim(system_prompt)) > 0),
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_ai_agents_client FOREIGN KEY (client_id)
        REFERENCES clients(id) ON DELETE CASCADE
);

-- O índice em client_id é mantido pois não há unique constraint simples para ele nesta tabela
CREATE INDEX IF NOT EXISTS idx_ai_agents_client_id ON ai_agents(client_id);

-- Comentários
COMMENT ON TABLE ai_agents IS 'Folha de pagamento digital: AI Employees operando para cada cliente.';
COMMENT ON COLUMN ai_agents.role IS 'Cargo do agente. Protegido por CHECK constraint.';
COMMENT ON COLUMN ai_agents.system_prompt IS 'O prompt mestre de contexto estrito deste funcionário.';


-- ==============================================================================
-- 2. Table: integrations
-- Finalidade: Centralizar chaves e credenciais B2B (OpenAI, Twilio, Google).
-- Desacopla secrets da tabela clients principal.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    provider TEXT NOT NULL CHECK (provider IN ('openai', 'twilio', 'evolution', 'google_calendar', 'anthropic')),
    credentials JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_integrations_client FOREIGN KEY (client_id)
        REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT uq_integrations_client_provider UNIQUE (client_id, provider)
);

-- Nota: O índice para client_id foi removido por ser redundante, 
-- já que a Unique Constraint (client_id, provider) cria implicitamente um índice utilizável.

-- Comentários
COMMENT ON TABLE integrations IS 'Registro de credenciais de APIs externas isoladas por cliente.';
COMMENT ON COLUMN integrations.provider IS 'Nome do provedor. Protegido por CHECK constraint.';
COMMENT ON COLUMN integrations.credentials IS 'JSON opaco com tokens/secrets de autenticação.';


-- ==============================================================================
-- 3. Table: business_rules
-- Finalidade: Policy Engine dinâmica baseada em chave-valor. 
-- Armazena preços, regras e FAQs sem gerar novas migrações estruturais.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS business_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    rules_data JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(rules_data) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_business_rules_client FOREIGN KEY (client_id)
        REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT uq_business_rules_client UNIQUE (client_id)
);

-- Nota: Índice redundante em client_id removido. A Unique Constraint já provê o índice B-Tree necessário.

-- Comentários
COMMENT ON TABLE business_rules IS 'Single Source of Truth dinâmica (JSONB) para regras de negócio do tenant.';
COMMENT ON COLUMN business_rules.rules_data IS 'Objeto JSON garantido pela constraint jsonb_typeof() = object.';

-- Fim da Migration 01
