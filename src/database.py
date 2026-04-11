import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class Database:
    def __init__(self):
        self.supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
    
    def get_active_routes(self):
        """Pega todas as rotas ativas para monitorar"""
        response = self.supabase.table("monitored_routes")\
            .select("*")\
            .eq("active", True)\
            .execute()
        return response.data
    
    def save_price(self, route_id: str, price: float, airline: str, url: str = None):
        """Salva preço no histórico"""
        data = {
            "route_id": route_id,
            "price": price,
            "airline": airline,
            "url": url,
            "found_at": datetime.now().isoformat()
        }
        return self.supabase.table("price_history").insert(data).execute()
    
    def get_last_price(self, route_id: str):
        """Pega o último preço registrado para uma rota"""
        response = self.supabase.table("price_history")\
            .select("price")\
            .eq("route_id", route_id)\
            .order("found_at", desc=True)\
            .limit(1)\
            .execute()
        
        if response.data:
            return response.data[0]["price"]
        return None
    
    def save_alert(self, route_id: str, price: float, message_id: int = None):
        """Registra que um alerta foi enviado"""
        data = {
            "route_id": route_id,
            "price": price,
            "telegram_message_id": message_id
        }
        return self.supabase.table("alerts_sent").insert(data).execute()
