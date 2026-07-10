import os
import httpx
import uvicorn
from fastapi import FastAPI, Request
from supabase import create_client
from openai import AsyncOpenAI
from app.services.crm_service import CRMService

app = FastAPI()
# Inicializa cliente. Se falhar na conexão, ele não trava o servidor.
try:
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY"))
except Exception as e:
    print(f"Erro ao inicializar Supabase: {e}")
    supabase = None

@app.post("/api/public/evolution-webhook")
@app.post("/api/public/evolution-webhook/")
async def webhook(request: Request):
    try:
        payload = await request.json()
        if payload.get('event') != 'messages.upsert':
            return {"status": "ok"}
        
        print("WEBHOOK MESSAGE RECEBIDO")
        
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
                print("CHAMANDO CRM SERVICE")
                # Dispara upsert silencioso
                CRMService.upsert_lead(supabase, client_id, raw_phone, remote_jid)
                # -------------------------------

                # IA
                ia = AsyncOpenAI(api_key=config['openai_api_key'])
                r = await ia.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "system", "content": config['system_prompt']}, {"role": "user", "content": texto}]
                )
                
                # Resposta
                evolution_url = os.environ.get("EVOLUTION_URL", "").rstrip('/')
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{evolution_url}/message/sendText/{instance_id}",
                        json={"number": remote_jid.split('@')[0], "text": r.choices[0].message.content},
                        headers={"apikey": config['api_key_evolution'], "Content-Type": "application/json"}
                    )
            else:
                print(f"ATENÇÃO: Nenhuma configuração encontrada para a instância {instance_id}")
                return {"status": "ok"}
        return {"status": "ok"}
    except Exception as e:
        print(f"ERRO CRÍTICO NO WEBHOOK: {e}")
        return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))