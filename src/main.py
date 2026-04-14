# -*- coding: utf-8 -*-
import os
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta
from flight_search import FlightSearch
from tarif_intelligence import TarifIntelligence

class FlightMonitor:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ ERRO CRÍTICO: Variáveis SUPABASE não encontradas!")
            return
            
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        self.flight_search = FlightSearch()
        self.tarif_intelligence = TarifIntelligence()
        
        # Sensibilidade: Alerta a partir de 15% de desconto
        self.min_discount_percent = 15 

    def get_monitored_routes(self):
        """Retorna as 3 rotas estratégicas para economizar créditos da API Free"""
        
        # TOP 3 ROTAS DE OURO (Alta demanda + Alta chance de oferta)
        strategic_routes = [
            {'id': 'GRU-LIS', 'origin': 'GRU', 'destination': 'LIS', 'max_price': 4500}, # Lisboa (Europa)
            {'id': 'GRU-MIA', 'origin': 'GRU', 'destination': 'MIA', 'max_price': 3800}, # Miami (EUA)
            {'id': 'GRU-CUN', 'origin': 'GRU', 'destination': 'CUN', 'max_price': 3200}  # Cancún (Caribe)
        ]
        
        return strategic_routes

    def save_price_history(self, route_id: str, price: float, airline: str):
        try:
            data = {
                "route_id": route_id,
                "price": price,
                "airline": airline,
                "currency": "BRL",
                "found_at": datetime.now().isoformat()
            }
            self.supabase.table("price_history").insert(data).execute()
        except Exception:
            pass

    def generate_google_flights_link(self, origin, destination, date_from, date_to):
        date_from_formatted = date_from.replace('-', '/')
        date_to_formatted = date_to.replace('-', '/')
        return (
            f"https://www.google.com/travel/flights?hl=pt-BR&gl=br&curr=BRL&tt=d"
            f"&sd={date_from_formatted}&ed={date_to_formatted}&d={origin}&r={destination}"
        )

    def send_smart_alert(self, route_id: str, price: float, analysis: dict, origin: str, destination: str, airline: str, date_from: str, date_to: str):
        try:
            google_link = self.generate_google_flights_link(origin, destination, date_from, date_to)
            savings = analysis['average_price'] - price
            discount = analysis['discount_percent']
            
            # ️ COLE SEU LINK DO GRUPO AQUI
            grupo_vip_link = "https://chat.whatsapp.com/EsFgvs6vuLE83qb9tx5dtn?mode=gi_t" 
            
            message = (
                f"🚨 *ALERTA VIP DETECTADO!* 🚨%0A%0A"
                f"✈️ *Rota:* {origin} → {destination}%0A"
                f"💰 *Preço:* R$ {price:.2f}%0A"
                f"📉 *Normal:* R$ {analysis['average_price']:.2f}%0A"
                f"💸 *Economia:* R$ {savings:.2f} ({discount}% OFF)%0A"
                f"🏢 *Cia:* {airline}%0A"
                f" *Ida/Volta:* {date_from.replace('-', '/')} a {date_to.replace('-', '/')}%0A%0A"
                f"⚠️ *Atenção:* Preço pode subir rápido!%0A"
                f" *Link para Comprar:*%0A{google_link}%0A%0A"
                f"👇 *Quer receber isso todo dia?* Entre no Grupo:%0A{grupo_vip_link}%0A"
                f"_Flight Monitor Pro_"
            )
            
            whatsapp_phone = "554199653041"  
            whatsapp_api_key = "6394803"     
            
            url_whatsapp = f"https://api.callmebot.com/whatsapp.php?phone={whatsapp_phone}&text={message}&apikey={whatsapp_api_key}"
            
            resp_wpp = requests.get(url_whatsapp, timeout=10)
            if resp_wpp.status_code == 200:
                print(f"   ✅ Alerta enviado para WhatsApp!")
            else:
                print(f"   ️ Erro WhatsApp: {resp_wpp.text}")

            # Salva no banco
            try:
                self.supabase.table("alerts_sent").insert({
                    "route_id": route_id, 
                    "price": price, 
                    "discount_percent": discount,
                    "classification": analysis['classification'], 
                    "sent_at": datetime.now().isoformat()
                }).execute()
            except Exception:
                pass
                
        except Exception as e:
            print(f"    ❌ Erro ao enviar: {e}")

    def run(self):
        print(f"🚀 Iniciando Monitoramento Diário (Top 3 Rotas) - {datetime.now()}")
        
        routes = self.get_monitored_routes()
        print(f" Focando em {len(routes)} rotas estratégicas...")
        
        success_count = 0
        
        for route in routes:
            try:
                route_id = route["id"]
                origin = route["origin"]
                destination = route["destination"]
                
                # DATAS DINÂMICAS: Sempre daqui a 4 semanas (28 dias)
                today = datetime.now()
                date_from = (today + timedelta(days=28)).strftime("%Y-%m-%d") 
                date_to = (today + timedelta(days=35)).strftime("%Y-%m-%d")   
                
                print(f"\n✈️ Verificando: {origin} → {destination} (Ida: {date_from})")
                
                flight_data = self.flight_search.get_flight_data(origin, destination, date_from, date_to)
                
                if flight_data and flight_data.get('price'):
                    price = flight_data['price']
                    airline = flight_data.get('airline', 'Desconhecida')
                    
                    print(f"   💰 Preço: R$ {price:.2f}")
                    
                    analysis = self.tarif_intelligence.analyze_tarif(origin, destination, price)
                    classification = analysis['classification']
                    discount = analysis['discount_percent']
                    
                    print(f"    Classificação: {classification} ({discount}%)")
                    
                    self.save_price_history(route_id, price, airline)
                    
                    # Envia alerta se tiver desconto >= 15% OU for classificado como oferta
                    if analysis['is_offer'] or discount >= self.min_discount_percent:
                        self.send_smart_alert(
                            route_id, price, analysis, 
                            origin, destination, airline, 
                            date_from, date_to
                        )
                        success_count += 1
                    else:
                        print(f"   ️ Preço dentro da média.")
                    
            except Exception as e:
                print(f"❌ Erro na rota {route_id}: {e}")
                continue
        
        print(f"\n{'='*40}")
        print(f"✅ Varredura concluída! {success_count} alertas enviados.")
        print(f"{'='*40}")

if __name__ == "__main__":
    try:
        monitor = FlightMonitor()
        monitor.run()
    except Exception as e:
        print(f"💥 Falha crítica: {e}")
