import requests

# Substitua com seus dados reais
INSTANCE_NAME = "SUA_INSTANCIA" # O nome da sua instância
API_KEY = "SUA_API_KEY_DA_EVOLUTION" # Sua chave de acesso
EVOLUTION_API_URL = "URL_DA_SUA_EVOLUTION_API" # Ex: https://api.sua-evolution.com
MEU_WEBHOOK_URL = "https://glamorous-sixtyfold-spew.ngrok-free.dev/api/webhook/whatsapp"

url = f"{EVOLUTION_API_URL}/webhook/set/{INSTANCE_NAME}"

payload = {
    "url": MEU_WEBHOOK_URL,
    "enabled": True,
    "events": ["messages.upsert"]
}

headers = {"apikey": API_KEY, "Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.json())