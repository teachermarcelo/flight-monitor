import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from flight_search import FlightSearch

class FlightMonitor:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.flight_search = FlightSearch()
        self.min_drop_percent = float(os.getenv("MIN_PRICE_DROP_PERCENT", 15))

    def get_monitored_routes(self):
        """Busca todas as rotas que devem ser monitoradas"""
        response = self.supabase.table("monitored_routes").select("*").execute()
        return response.data

    def save_price_history(self, route_id: str, price: float, airline: str):
        """Salva o preço encontrado no histórico"""
        try:
            data = {
                "route_id": route_id,
                "price": price,
                "airline": airline,
                "currency": "BRL",
                "found_at": datetime.now().isoformat()
            }
            self.supabase.table("price_history").insert(data).execute()
            print(f"💾 Preço salvo no banco: R$ {price:.2f}")
        except Exception as e:
            print(f"❌ Erro ao salvar no banco: {e}")

    def check_alerts(self, route_id: str, current_price: float, max_price: float):
        """Verifica se o preço caiu o suficiente para alertar"""
        drop_percentage = ((max_price - current_price) / max_price) * 100
        
        if drop_percentage >= self.min_drop_percent:
            print(f"🔥 OFERTA! Queda de {drop_percentage:.1f}% na rota {route_id}")
            # Aqui poderíamos salvar na tabela de alertas ou enviar email
            try:
                alert_data = {
                    "route_id": route_id,
                    "price": current_price,
                    "message": f"Preço caiu {drop_percentage:.1f}%! De R$ {max_price:.2f} para R$ {current_price:.2f}",
                    "sent_at": datetime.now().isoformat()
                }
                self.supabase.table("alerts_sent").insert(alert_data).execute()
            except Exception as e:
                print(f"❌ Erro ao salvar alerta: {e}")

    def run(self):
        """Loop principal do monitoramento"""
        print(f"🚀 Iniciando monitoramento - {datetime.now()}")
        
        routes = self.get_monitored_routes()
        print(f"📋 {len(routes)} rotas para monitorar")
        
        for route in routes:
            route_id = route["id"]
            origin = route["origin"]
            destination = route["destination"]
            max_price = route["max_price"]
            
            print(f"Verificando: {origin} → {destination}")
            
            try:
                # CORREÇÃO AQUI: Chamando o método get_flight_data com as datas certas
                today = datetime.now()
                date_from = (today + timedelta(days=7)).strftime("%Y-%m-%d")  # Daqui a 7 dias
date_to = (today + timedelta(days=14)).strftime("%Y-%m-%d")   # Volta após 7 dias
                
                flight_data = self.flight_search.get_flight_data(origin, destination, date_from, date_to)
                
                if flight_data and flight_data.get('price'):
                    price = flight_data['price']
                    airline = flight_data.get('airline', 'Desconhecida')
                    
                    # Salva no histórico
                    self.save_price_history(route_id, price, airline)
                    
                    # Verifica se é oferta
                    self.check_alerts(route_id, price, max_price)
                else:
                    print(f"⚠️ Nenhum preço válido encontrado para {origin} → {destination}")
                    
            except Exception as e:
                print(f"❌ Erro ao verificar rota {route_id}: {e}")
                
        print("✅ Monitoramento concluído.")

if __name__ == "__main__":
    monitor = FlightMonitor()
    monitor.run()
