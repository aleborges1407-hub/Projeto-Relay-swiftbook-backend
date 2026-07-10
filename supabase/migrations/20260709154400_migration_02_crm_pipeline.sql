-- ==============================================================================
-- Migration: 02 - CRM Pipeline (Enterprise Edition)
-- Description: Criação das tabelas centrais do CRM e Engajamento
-- (leads, appointments).
-- Dependências: Requer Migration 01 (clients, ai_agents).
-- Nota: RLS desabilitado nesta fase.
-- ==============================================================================

-- ==============================================================================
-- 4. Table: leads
-- Finalidade: Cadastro mestre de consumidores para Home Services. 
-- Centraliza tracking, omnichanel e CRM Pipeline.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    external_id TEXT,
    phone TEXT NOT NULL,
    name TEXT,
    email TEXT,
    status TEXT NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'engaging', 'qualified', 'scheduled', 'won', 'lost')),
    value NUMERIC(10, 2),
    address TEXT,
    service_requested TEXT,
    source TEXT,
    assigned_ai UUID,
    last_message_at TIMESTAMPTZ,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(tags) = 'array'),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb CHECK (jsonb_typeof(metadata) = 'object'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_leads_client FOREIGN KEY (client_id)
        REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT fk_leads_agent FOREIGN KEY (assigned_ai)
        REFERENCES ai_agents(id) ON DELETE SET NULL,
    CONSTRAINT uq_leads_client_phone UNIQUE (client_id, phone)
);

-- Índices para leads
CREATE INDEX IF NOT EXISTS idx_leads_client_status ON leads(client_id, status);
-- Nota: O índice em client_id_phone é redundante devido à uq_leads_client_phone

-- Comentários
COMMENT ON TABLE leads IS 'CRM de consumidores finais, centralizando pipeline de status B2B.';
COMMENT ON COLUMN leads.external_id IS 'ID externo omnichanel (WhatsApp, Instagram, Telegram).';
COMMENT ON COLUMN leads.phone IS 'Chave natural de contato para SMS/WhatsApp.';
COMMENT ON COLUMN leads.value IS 'Valor estimado/fechado do serviço em precisão exata.';
COMMENT ON COLUMN leads.tags IS 'Array JSON para tagueamento flexível (ex: VIP, problem_client).';


-- ==============================================================================
-- 5. Table: appointments
-- Finalidade: Fonte da verdade dos compromissos e agendamentos convertidos.
-- Sincroniza com APIs de calendário de terceiros via event_id.
-- ==============================================================================
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    service_type TEXT NOT NULL,
    price NUMERIC(10, 2),
    status TEXT NOT NULL DEFAULT 'confirmed' CHECK (status IN ('confirmed', 'rescheduled', 'cancelled', 'completed')),
    calendar_provider TEXT NOT NULL CHECK (calendar_provider IN ('google', 'outlook', 'apple', 'internal')),
    provider_event_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT fk_appointments_client FOREIGN KEY (client_id)
        REFERENCES clients(id) ON DELETE CASCADE,
    CONSTRAINT fk_appointments_lead FOREIGN KEY (lead_id)
        REFERENCES leads(id) ON DELETE CASCADE
);

-- Índices para appointments
CREATE INDEX IF NOT EXISTS idx_appointments_client_id ON appointments(client_id);
CREATE INDEX IF NOT EXISTS idx_appointments_lead_id ON appointments(lead_id);
CREATE INDEX IF NOT EXISTS idx_appointments_schedule ON appointments(client_id, start_time);

-- Comentários
COMMENT ON TABLE appointments IS 'Registro transacional de agendamentos. Preparado para evolução futura (alocação de múltiplos profissionais/recursos via tabela associativa).';
COMMENT ON COLUMN appointments.start_time IS 'Timestamp UTC com timezone exigido pelo B2B Calendar.';
COMMENT ON COLUMN appointments.calendar_provider IS 'Fornecedor de sync do evento para abster Lock-in.';

-- Fim da Migration 02
