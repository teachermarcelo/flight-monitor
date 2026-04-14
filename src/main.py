# -*- coding: utf-8 -*-
import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from flight_search import FlightSearch
from tarif_intelligence import TarifIntelligence
from telegram_bot import TelegramAlertBot

class FlightMonitor:
    def __init__(self):
        # Configuração do Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ ERRO CRÍTICO: Variáveis de ambiente SUPABASE_URL ou SUPABASE_KEY não encontradas!")
            return
            
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Inicialização dos módulos
        self.flight_search = FlightSearch()
        self.tarif_intelligence = TarifIntelligence()
        self.telegram_bot = TelegramAlertBot()
        
        # Configurações
        self.min_drop_percent = float(os.getenv("MIN_PRICE_DROP_PERCENT", 15))

    def get_monitored_routes(self):
        """Busca todas as rotas que devem ser monitoradas"""
        try:
            response = self.supabase.table("monitored_routes").select("*").execute()
            return response.data
        except Exception as e:
            print(f"❌ Erro ao buscar rotas no Supabase: {e}")
            return []

    def save_price_history(self, route_id: str, price: float, airline: str):
        """Salva o preço no histórico de forma segura"""
        try:
            data = {
                "route_id": route_id,
                "price": price,
                "airline": airline,
                "currency": "BRL",
                "found_at": datetime.now().isoformat()
            }
            
            self.supabase.table("price_history").insert(data).execute()
            # Não imprime aqui para não poluir o log
        except Exception as e:
            print(f"   ❌ Erro ao salvar histórico: {e}")

    def generate_google_flights_link(self, origin, destination, date_from, date_to):
        """Gera link funcional do Google Flights com datas corretas"""
        # Formata datas para o formato YYYY/MM/DD que o Google aceita
        date_from_formatted = date_from.replace('-', '/')
        date_to_formatted = date_to.replace('-', '/')
        
        link = (
            f"https://www.google.com/travel/flights?"
            f"hl=pt-BR&gl=br&curr=BRL"
            f"&tt=d"
            f"&sd={date_from_formatted}"
            f"&ed={date_to_formatted}"
            f"&d={origin}"
            f"&r={destination}"
        )
        return link

    def send_smart_alert(self, route_id: str, price: float, analysis: dict, origin: str, destination: str, airline: str, date_from: str, date_to: str):
        """Envia alerta inteligente via Telegram e salva no banco"""
        try:
            # Gera link do Google Flights
            google_link = self.generate_google_flights_link(origin, destination, date_from, date_to)
            
            # Envia via Telegram
            self.telegram_bot.send_alert(
                route_origin=origin,
                route_dest=destination,
                current_price=price,
                avg_price=analysis['average_price'],
                discount_percent=analysis['discount_percent'],
                classification=analysis['classification'],
                airline=airline,
                google_link=google_link
            )
            
            # Salva no banco também
            alert_data = {
                "route_id": route_id,
                "price": price,
                "message": analysis['message'],
                "discount_percent": analysis['discount_percent'],
                "classification": analysis['classification'],
                "sent_at": datetime.now().isoformat()
            }
            self.supabase.table("alerts_sent").insert(alert_data).execute()
            
            print(f"   🔔 ALERTA ENVIADO COM SUCESSO!")
            print(f"      📢 Mensagem: {analysis['message']}")
            print(f"      🔗 Link: {google_link}")
            
        except Exception as e:
            print(f"    ❌ Erro ao enviar alerta: {e}")

    def run(self):
        """Loop principal do monitoramento com Inteligência de Tarifas"""
        print(f"🚀 Iniciando monitoramento inteligente - {datetime.now()}")
        
        routes = self.get_monitored_routes()
        
        if not routes:
            print("⚠️ Nenhuma rota encontrada para monitorar.")
            return

        print(f"📋 {len(routes)} rotas carregadas para verificação...")
        
        success_count = 0
        error_count = 0
        
        for route in routes:
            try:
                route_id = route["id"]
                origin = route["origin"]
                destination = route["destination"]
                max_price_config = route["max_price"]
                
                print(f"\n{'-'*40}")
                print(f"✈️ Verificando: {origin} → {destination}")
                
                # Define datas da busca (daqui 7 dias, volta após 7 dias)
                today = datetime.now()
                date_from = (today + timedelta(days=7)).strftime("%Y-%m-%d")
                date_to = (today + timedelta(days=14)).strftime("%Y-%m-%d")
                
                # 1. Busca dados do voo
                flight_data = self.flight_search.get_flight_data(origin, destination, date_from, date_to)
                
                if flight_data and flight_data.get('price'):
                    price = flight_data['price']
                    airline = flight_data.get('airline', 'Desconhecida')
                    
                    print(f"   💰 Preço Encontrado: R$ {price:.2f} ({airline})")
                    
                    # 2. ANÁLISE DE INTELIGÊNCIA DE TARIFA
                    analysis = self.tarif_intelligence.analyze_tarif(origin, destination, price)
                    
                    classification = analysis['classification']
                    discount = analysis['discount_percent']
                    
                    print(f"   🧠 Classificação: {classification}")
                    print(f"   📉 Desconto vs Média: {discount}%")
                    
                    if analysis['message']:
                        print(f"   💬 {analysis['message']}")
                    
                    # 3. Salva no histórico
                    self.save_price_history(route_id, price, airline)
                    
                    # 4. Dispara Alertas Inteligentes
                    if analysis['is_offer']:
                        if classification in ['ERRO_TARIFA_PROVAVEL', 'OFERTA_EXCELENTE', 'OFERTA_BOA']:
                            self.send_smart_alert(
                                route_id, price, analysis, 
                                origin, destination, airline, 
                                date_from, date_to
                            )
                        else:
                            print(f"   👍 Oferta leve detectada, mas abaixo do threshold crítico.")
                    else:
                        print(f"   ⚖️ Preço dentro da normalidade de mercado.")
                    
                    success_count += 1
                    
                else:
                    print(f"   ⚠️ Nenhum preço válido retornado pela busca.")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ Erro inesperado ao processar rota {route.get('id', 'unknown')}: {e}")
                error_count += 1
                continue
        
        print(f"\n{'='*40}")
        print(f"✅ Monitoramento concluído!")
        print(f"📊 Sucessos: {success_count} | Erros/Sem Preço: {error_count}")
        print(f"{'='*40}")

if __name__ == "__main__":
    try:
        monitor = FlightMonitor()
        monitor.run()
    except Exception as e:
        print(f"💥 Falha crítica ao iniciar o monitor: {e}")
