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
