# Relay Backend (FastAPI + LangGraph)

Este é o backend do AI Appointment Setter. Ele recebe requisições do frontend, captura Webhooks via Twilio, processa o agente através do LangGraph e salva logs no Supabase.

## Como Rodar Localmente

1. Clone o repositório.
2. Copie o arquivo `.env.example` para `.env` e preencha suas variáveis:
   `cp .env.example .env`
3. Certifique-se de ter o Docker instalado.
4. Execute o build e levante os serviços:
   `docker-compose up --build`

Isso iniciará:
- **Redis** na porta `6379`
- **FastAPI** na porta `8000`

Para testar se está vivo, abra `http://localhost:8000/health`.

## Variáveis de Ambiente Necessárias (Railway / Render)

Ao realizar o deploy, você precisará configurar as seguintes variáveis no painel da plataforma:

| Variável | Descrição |
|----------|-----------|
| `OPENAI_API_KEY` | Chave da OpenAI para instanciar o `gpt-4o-mini`. |
| `SUPABASE_URL` | URL pública do seu banco Supabase. |
| `SUPABASE_KEY` | Chave `service_role` (para permissões completas) do Supabase. |
| `TWILIO_SID` | Account SID do console do Twilio. |
| `TWILIO_TOKEN` | Auth Token do console do Twilio. |
| `TWILIO_PHONE_NUMBER` | O número de telefone comprado (ex: `+1234567890`). |
| `GOOGLE_CALENDAR_CREDENTIALS`| O JSON da service account do Google Cloud codificado em Base64. |
| `REDIS_URL` | URL de conexão com um Redis gerenciado (ex: gerado automaticamente pela Railway ou por serviços como Upstash). |

## Endpoint do Webhook
Configure o Twilio para enviar requisições `POST` para `https://<seu-dominio-deploy>.railway.app/api/webhook/twilio` quando um SMS chegar.