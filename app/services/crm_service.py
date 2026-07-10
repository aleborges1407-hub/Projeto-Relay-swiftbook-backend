import traceback

class CRMService:
    @staticmethod
    def upsert_lead(supabase_client, client_id: str, phone: str, external_id: str = None):
        """
        Creates a new lead if it doesn't exist. If it exists, updates last_message_at without changing status.
        Uses UQ constraint logical matching (client_id + phone).
        """
        if not supabase_client:
            print("[CRM] Erro: Cliente Supabase nulo no serviço.")
            return None
            
        print(f"CLIENT_ID RECEBIDO: {client_id}")
        print(f"TELEFONE RECEBIDO: {phone}")
            
        try:
            # 1. Busca o lead existente
            res = supabase_client.table('leads').select('id, status').eq('client_id', client_id).eq('phone', phone).execute()
            
            if res.data and len(res.data) > 0:
                # O Lead já existe. Apenas atualiza a última interação.
                lead_id = res.data[0]['id']
                import datetime
                now_iso = datetime.datetime.utcnow().isoformat()
                
                update_res = supabase_client.table('leads').update({
                    'last_message_at': now_iso
                }).eq('id', lead_id).execute()
                
                print(f"RESPOSTA SUPABASE (UPDATE): {update_res.data}")
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
                    print(f"RESPOSTA SUPABASE (INSERT): {insert_res.data}")
                    return insert_res.data[0]['id']
                else:
                    print(f"ERRO: Supabase não retornou dados após tentativa de inserção.")
        except Exception as e:
            print(f"ERRO COMPLETO: {e}")
            traceback.print_exc()
        
        return None
