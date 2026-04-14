# -*- coding: utf-8 -*-
import os
import requests
from supabase import create_client, Client
from datetime import datetime, timedelta
from flight_search import FlightSearch
from tarif_intelligence import TarifIntelligence

class FlightMonitor:
    def __init__(self):
        # Configuração do Supabase
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            print("❌ ERRO CRÍTICO: Variáveis de ambiente SUPABASE não encontradas!")
            return
            
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        
        # Inicialização dos módulos
        self.flight_search = FlightSearch()
        self.tarif_intelligence = TarifIntelligence()
        
        # Configurações de Sensibilidade (AUMENTADA para mais alertas)
        # Agora considera ofertas a partir de 15% de desconto
        self.min_discount_percent = 15 

    def get_monitored_routes(self):
        """Busca rotas do banco OU usa lista expandida interna se o banco estiver vazio"""
        try:
            response = self.supabase.table("monitored_routes").select("*").execute()
            if response.data and len(response.data) > 0:
                return response.data
        except Exception as e:
            print(f"️ Erro ao buscar no DB, usando lista interna: {e}")

        # LISTA EXPANDIDA DE ROTAS (Fallback Automático)
        # Origens Brasileiras
        origins = ['GRU', 'GIG', 'BSB', 'CGH', 'VCP', 'CWB', 'POA', 'FLN', 'SSA', 'REC', 'FOR', 'MAO', 'BEL', 'CNF', 'GYN', 'SDU']
        # Destinos Internacionais (EUA, Europa, Caribe, América do Sul)
        destinations = [
            'MIA', 'MCO', 'JFK', 'EWR', 'LAX', 'SFO', 'ORD', 'IAH', 'ATL', 'BOS', 'LAS', 'SEA', 'DFW',
            'LIS', 'OPO', 'MAD', 'BCN', 'CDG', 'ORY', 'FCO', 'MXP', 'VCE', 'LHR', 'LGW', 'AMS', 'FRA', 'DUB', 'BRU', 'ZRH', 'VIE', 'PRG', 'WAW', 'ATH', 'IST',
            'CUN', 'PUJ', 'HAV', 'PTY', 'BOG', 'LIM', 'SCL', 'EZE', 'BRC', 'MDZ', 'MVD', 'ASU', 'UIO', 'GYE'
        ]
        
        routes = []
        # Gera combinações (pode filtrar algumas se quiser evitar rotas sem sentido, ex: Manaus -> Bariloche direto é raro, mas o buscador trata)
        # Aqui vamos criar uma lista inteligente das mais populares para não estourar limites de API gratuita
        popular_routes = [
            ('GRU', 'LIS'), ('GRU', 'MAD'), ('GRU', 'BCN'), ('GRU', 'CDG'), ('GRU', 'LHR'), ('GRU', 'MIA'), ('GRU', 'MCO'), ('GRU', 'JFK'), ('GRU', 'EZE'), ('GRU', 'CUN'), ('GRU', 'PUJ'),
            ('GIG', 'LIS'), ('GIG', 'MIA'), ('GIG', 'MCO'), ('GIG', 'CDG'), ('GIG', 'EZE'),
            ('BSB', 'LIS'), ('BSB', 'MIA'), ('BSB', 'EZE'),
            ('CWB', 'LIS'), ('CWB', 'MIA'), ('CWB', 'EZE'), ('CWB', 'BRC'),
            ('POA', 'EZE'), ('POA', 'MVD'), ('POA', 'LIS'), ('POA', 'MIA'),
            ('SSA', 'LIS'), ('SSA', 'MIA'), ('SSA', 'MAD'),
            ('FOR', 'LIS'), ('FOR', 'MIA'), ('FOR', 'MAD'),
            ('REC', 'LIS'), ('REC', 'MIA'), ('REC', 'MAD'),
            ('MAO', 'MIA'), ('MAO', 'LIS'), ('MAO', 'MAD'),
            ('FLN', 'EZE'), ('FLN', 'MIA'), ('FLN', 'LIS')
        ]
        
        for origin, dest in popular_routes:
            routes.append({
                "id": f"{origin}-{dest}", # ID temporário se não vier do DB
                "origin": origin,
                "destination": dest,
                "max_price": 5000 # Preço teto genérico para cálculo de % (ajustável no DB depois)
            })
            
        return routes

    def save_price_history(self, route_id: str, price: float, airline: str):
        """Salva o preço no histórico"""
        try:
            data = {
                "route_id": route_id,
                "price": price,
                "airline": airline,
                "currency": "BRL",
                "found_at": datetime.now().isoformat()
            }
            self.supabase.table("price_history").insert(data).execute()
        except Exception as e:
            pass # Silencioso para não poluir log

    def generate_google_flights_link(self, origin, destination, date_from, date_to):
        """Gera link do Google Flights"""
        date_from_formatted = date_from.replace('-', '/')
        date_to_formatted = date_to.replace('-', '/')
        return (
            f"https://www.google.com/travel/flights?hl=pt-BR&gl=br&curr=BRL&tt=d"
            f"&sd={date_from_formatted}&ed={date_to_formatted}&d={origin}&r={destination}"
        )

    def send_smart_alert(self, route_id: str, price: float, analysis: dict, origin: str, destination: str, airline: str, date_from: str, date_to: str):
        """Envia alerta via WhatsApp (Mais frequente agora)"""
        try:
            google_link = self.generate_google_flights_link(origin, destination, date_from, date_to)
            savings = analysis['average_price'] - price
            discount = analysis['discount_percent']
            
            # Link do Grupo VIP
            grupo_vip_link = "https://chat.whatsapp.com/SEU_CODIGO_DO_GRUPO_AQUI" 
            
            message = (
                f"🚨 *ALERTA DE OFERTA!* 🚨%0A%0A"
                f"✈️ *Rota:* {origin} → {destination}%0A"
                f"💰 *Preço:* R$ {price:.2f}%0A"
                f" *Normal:* R$ {analysis['average_price']:.2f}%0A"
                f"💸 *Economia:* R$ {savings:.2f} ({discount}% OFF)%0A"
                f" *Cia:* {airline}%0A"
                f"📅 *Ida/Volta:* {date_from.replace('-', '/')} a {date_to.replace('-', '/')}%0A%0A"
                f"⚠️ *Atenção:* Preço pode mudar rápido!%0A"
                f"🔗 *Link para Comprar:*%0A{google_link}%0A%0A"
                f" *Quer mais ofertas assim?* Entre no Grupo:%0A{grupo_vip_link}%0A"
                f"_Flight Monitor Pro_"
            )
            
            whatsapp_phone = "554199653041"  
            whatsapp_api_key = "6394803"     
            
            url_whatsapp = f"https://api.callmebot.com/whatsapp.php?phone={whatsapp_phone}&text={message}&apikey={whatsapp_api_key}"
            
            resp_wpp = requests.get(url_whatsapp, timeout=10)
            if resp_wpp.status_code == 200:
                print(f"   ✅ Alerta enviado para WhatsApp!")
            else:
                print(f"   ⚠️ Erro WhatsApp: {resp_wpp.text}")

            # Salva no banco
            alert_data = {
                "route_id": route_id,
                "price": price,
                "message": f"Oferta de {discount}% detectada",
                "discount_percent": discount,
                "classification": analysis['classification'],
                "sent_at": datetime.now().isoformat()
            }
            try:
                self.supabase.table("alerts_sent").insert(alert_data).execute()
            except:
                pass
                
        except Exception as e:
            print(f"    Erro ao enviar: {e}")

    def run(self):
        """Loop principal"""
        print(f"🚀 Iniciando monitoramento FREQUENTE - {datetime.now()}")
        
        routes = self.get_monitored_routes()
        print(f"📋 {len(routes)} rotas para verificar...")
        
        success_count = 0
        
        for route in routes:
            try:
                route_id = route.get("id", f"{route['origin']}-{route['destination']}")
                origin = route["origin"]
                destination = route["destination"]
                
                # DATAS DINÂMICAS: Daqui a 4 semanas (28 dias) ida e volta + 7 dias
                today = datetime.now()
                date_from = (today + timedelta(days=28)).strftime("%Y-%m-%d") # Ida: 4 semanas
                date_to = (today + timedelta(days=35)).strftime("%Y-%m-%d")   # Volta: 5 semanas
                
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
                    
                    # LÓGICA DE ALERTA EXPANDIDA
                    # Envia se for Oferta Leve (>15%), Boa, Excelente ou Erro
                    # Isso aumenta drasticamente a quantidade de alertas
                    if analysis['is_offer'] or discount >= self.min_discount_percent:
                        if classification in ['ERRO_TARIFA_PROVAVEL', 'OFERTA_EXCELENTE', 'OFERTA_BOA', 'OFERTA_LEVE']:
                            self.send_smart_alert(
                                route_id, price, analysis, 
                                origin, destination, airline, 
                                date_from, date_to
                            )
                            success_count += 1
                        else:
                            print(f"   👍 Oferta leve, mas ignorada pela classificação.")
                    else:
                        print(f"   ⚖️ Preço normal.")
                    
            except Exception as e:
                print(f"❌ Erro na rota {route.get('origin')}: {e}")
                continue
        
        print(f"\n{'='*40}")
        print(f"✅ Monitoramento concluído! {success_count} alertas enviados.")
        print(f"{'='*40}")

if __name__ == "__main__":
    try:
        monitor = FlightMonitor()
        monitor.run()
    except Exception as e:
        print(f" Falha crítica: {e}")
