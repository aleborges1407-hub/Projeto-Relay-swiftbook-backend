import datetime
import traceback
class CRMService:
    @staticmethod
    def upsert_lead(supabase_client, client_id: str, phone: str, external_id: str = None):
        """
        Creates a new lead if it doesn't exist. If it exists, updates last_message_at without changing status.
        Uses UQ constraint logical matching (client_id + phone).
        """
        if not supabase_client:
            return None
            
        try:
            # 1. Busca o lead existente
            res = supabase_client.table('leads').select('id, status').eq('client_id', client_id).eq('phone', phone).execute()
            
            if res.data and len(res.data) > 0:
                # O Lead já existe. Apenas atualiza a última interação.
                lead_id = res.data[0]['id']
                now_iso = datetime.datetime.utcnow().isoformat()
                
                update_res = supabase_client.table('leads').update({
                    'last_message_at': now_iso
                }).eq('id', lead_id).execute()
                
                return lead_id
            else:
                # 2. Criação de novo lead
                new_lead = {
                    'client_id': client_id,
                    'phone': phone,
                    'external_id': external_id or phone,
                    'status': 'new',
                    'source': 'whatsapp',
                }
                insert_res = supabase_client.table('leads').insert(new_lead).execute()
                if insert_res.data:
                    return insert_res.data[0]['id']
        except Exception:
            traceback.print_exc()
        
        return None
    
    @staticmethod
    def save_message(supabase_client, client_id: str, lead_id: str, role: str, content: str):
        """
        Saves a message to the messages table.
        """
        if not supabase_client:
            return None
            
        try:
            msg_data = {
                'client_id': client_id,
                'lead_id': lead_id,
                'role': role,
                'content': content
            }
            res = supabase_client.table('messages').insert(msg_data).execute()
            if res.data:
                return res.data[0]['id']
        except Exception:
            traceback.print_exc()
        
        return None

    @staticmethod
    def get_recent_messages(supabase_client, client_id: str, lead_id: str, limit: int = 20):
        """
        Fetches recent messages from the database and maps them to LangChain message objects.
        Returns them in chronological order (oldest to newest).
        """
        from langchain_core.messages import HumanMessage, AIMessage
        
        if not supabase_client:
            return []
        try:
            res = supabase_client.table('messages').select('role, content').eq('client_id', client_id).eq('lead_id', lead_id).order('created_at', desc=True).limit(limit).execute()
            if not res.data:
                return []
            
            # Reverse to chronological order
            ordered_data = list(reversed(res.data))
            
            messages = []
            for msg in ordered_data:
                if msg['role'] == 'user':
                    messages.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    messages.append(AIMessage(content=msg['content']))
            return messages
        except Exception:
            traceback.print_exc()
            
        return []

    @staticmethod
    def get_ai_config(supabase_client, client_id: str):
        """
        Fetches the AI configuration for the specified client.
        """
        if not supabase_client:
            return None
        try:
            res = supabase_client.table('ai_configs').select('*').eq('client_id', client_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception:
            traceback.print_exc()
            
        return None
