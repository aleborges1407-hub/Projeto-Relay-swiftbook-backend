import asyncio
import os

import httpx
import uvicorn
from fastapi import FastAPI, Request
from supabase import create_client

from app.agent import process_message
from app.services.crm_service import CRMService

app = FastAPI()
# Inicializa cliente. Se falhar na conexão, ele não trava o servidor.
try:
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY"))
except Exception:
    supabase = None

@app.post("/api/public/evolution-webhook")
@app.post("/api/public/evolution-webhook/")
async def webhook(request: Request):
    try:
        payload = await request.json()
        if payload.get('event') != 'messages.upsert':
            return {"status": "ok"}
        
        data = payload.get('data', {})
        instance_id = payload.get('instance')
        msg = data.get('message', {})
        texto = msg.get('conversation') or msg.get('extendedTextMessage', {}).get('text', '')
        remote_jid = data.get('key', {}).get('remoteJid', '')
        from_me = data.get('key', {}).get('fromMe', False)

        # TRAVA VITAL RESTAURADA: 'not from_me' evita erro 502 por loop infinito
        if texto and supabase and not from_me:
            # Busca configs sem erro fatal (.single() retirado para evitar erro se não achar)
            res = supabase.table("clients").select("*").eq("instance_key", instance_id).execute()
            
            if res.data and len(res.data) > 0:
                config = res.data[0] # Pega o primeiro resultado encontrado
                
                # --- INGESTAO DE LEADS (CRM) ---
                raw_phone = remote_jid.split('@')[0] if remote_jid else "unknown"
                client_id = config['id']
                # Dispara upsert silencioso e pega o lead_id
                lead_id = CRMService.upsert_lead(supabase, client_id, raw_phone, remote_jid)
                # -------------------------------

                if lead_id:
                    # Salva a mensagem do usuário
                    CRMService.save_message(supabase, client_id, lead_id, "user", texto)

                # Busca AI Config e Memória
                ai_config = CRMService.get_ai_config(supabase, client_id)
                memory_messages = CRMService.get_recent_messages(supabase, client_id, lead_id, limit=20) if lead_id else []

                # IA usando o agente LangGraph
                # Executa num thread pool para não travar o FastAPI
                reply, _ = await asyncio.to_thread(
                    process_message,
                    phone=raw_phone,
                    user_message=texto,
                    api_key=config['openai_api_key'],
                    ai_config=ai_config,
                    current_state=None,
                    memory_messages=memory_messages
                )
                
                if lead_id:
                    # Salva a resposta da IA
                    CRMService.save_message(supabase, client_id, lead_id, "assistant", reply)
                
                # Resposta
                evolution_url = os.environ.get("EVOLUTION_URL", "").rstrip('/')
                if evolution_url and not evolution_url.startswith("http"):
                    evolution_url = f"https://{evolution_url}"
                
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{evolution_url}/message/sendText/{instance_id}",
                        json={"number": remote_jid.split('@')[0], "text": reply},
                        headers={"apikey": os.environ.get("EVOLUTION_API_KEY", ""), "Content-Type": "application/json"}
                    )
            else:
                return {"status": "ok"}
        return {"status": "ok"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))