CREATE TABLE IF NOT EXISTS ai_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    company_name TEXT,
    business_type TEXT,
    base_prompt TEXT,
    tone TEXT,
    business_rules TEXT,
    products_services TEXT,
    faq TEXT,
    opening_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,

    CONSTRAINT uq_ai_configs_client_id UNIQUE (client_id)
);

CREATE INDEX IF NOT EXISTS idx_ai_configs_client_id ON ai_configs(client_id);
