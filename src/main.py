import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

from database import Database
from flight_search import FlightSearch
from telegram_bot import TelegramBot

load_dotenv()

class FlightMonitor:
    def __init__(self):
        self.db = Database()
        self.flight_search = FlightSearch()
        self.bot = TelegramBot()
               # Tenta pegar o segredo, mas garante que seja 15 se der erro
        self.min_drop_percent = 15.0 
        try:
            val = os.getenv("MIN_PRICE_DROP_PERCENT")
            if val:
                self.min_drop_percent = float(val)
        except:
            pass
    
    def check_route(self, route):
        """Verifica uma rota específica"""
        print(f"Verificando: {route['origin']} → {route['destination']}")
        
        # Define datas (padrão: daqui a 30 dias para 7 dias de viagem)
        departure = route.get('departure_date') or (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        return_date = route.get('return_date') or (datetime.now() + timedelta(days=37)).strftime('%Y-%m-%d')
        
        # Garante formato de data string
        if isinstance(departure, datetime):
            departure = departure.strftime('%Y-%m-%d')
        if isinstance(return_date, datetime):
            return_date = return_date.strftime('%Y-%m-%d')
        
        # Busca voos
        flight = self.flight_search.search_flights(
            origin=route['origin'],
            destination=route['destination'],
            departure_date=departure,
            return_date=return_date
        )
        
        if not flight:
            print("Nenhum voo encontrado")
            return
        
        # Salva preço no histórico
        self.db.save_price(
            route_id=route['id'],
            price=flight['price'],
            airline=flight['airline']
        )
        
        # Pega último preço para comparação
        last_price = self.db.get_last_price(route['id'])
        
        # Lógica de alerta
        is_good_deal = False
        
        # Se tem preço máximo definido e bateu a meta
        if route.get('max_price') and flight['price'] <= route['max_price']:
            is_good_deal = True
            print(f"✅ Preço abaixo do máximo! R$ {flight['price']} <= R$ {route['max_price']}")
        
        # Se o preço caiu consideravelmente em relação à última busca
        if last_price:
            drop_percent = ((last_price - flight['price']) / last_price) * 100
            if drop_percent >= self.min_drop_percent:
                is_good_deal = True
                print(f"✅ Queda de {drop_percent:.1f}% detectada!")
        
        # Envia alerta
        if is_good_deal:
            message_id = self.bot.send_flight_alert(
                origin=route['origin'],
                destination=route['destination'],
                price=flight['price'],
                airline=flight['airline'],
                departure=departure,
                old_price=last_price
            )
            
            if message_id:
                self.db.save_alert(route['id'], flight['price'], message_id)
                print(f"📢 Alerta enviado!")
    
    def run(self):
        """Executa o monitoramento de todas as rotas"""
        print(f"🚀 Iniciando monitoramento - {datetime.now()}")
        
        routes = self.db.get_active_routes()
        print(f"📋 {len(routes)} rotas para monitorar")
        
        for route in routes:
            try:
                self.check_route(route)
            except Exception as e:
                print(f"❌ Erro ao verificar rota {route['id']}: {e}")
                continue
        
        print("✅ Monitoramento concluído.")

if __name__ == "__main__":
    monitor = FlightMonitor()
    monitor.run()
