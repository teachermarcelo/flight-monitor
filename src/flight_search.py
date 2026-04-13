import os
import requests
import random
from datetime import datetime

class FlightSearch:
    def __init__(self):
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.api_host = os.getenv("RAPIDAPI_HOST")
        
        if not self.api_key or not self.api_host:
            print("❌ Credenciais da RapidAPI não encontradas!")
            self.client = None
        else:
            self.client = True
            self.headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            self.base_url = f"https://{self.api_host}"
        
        # Tabela de preços de referência (fallback realista)
        self.reference_prices = {
            ('GRU', 'LIS'): (2800, 4500),
            ('GRU', 'MCO'): (2300, 3900),
            ('GRU', 'MIA'): (2200, 3800),
            ('GRU', 'JFK'): (2500, 4200),
            ('GRU', 'CDG'): (2600, 4300),
            ('GRU', 'MAD'): (2400, 4000),
            ('GRU', 'BCN'): (2500, 4100),
            ('GRU', 'LHR'): (2700, 4400),
            ('GRU', 'FCO'): (2600, 4200),
            ('GRU', 'AMS'): (2650, 4300),
            ('GRU', 'EZE'): (800, 1500),
            ('GRU', 'SCL'): (900, 1600),
            ('GIG', 'MIA'): (2300, 3900),
            ('GIG', 'LIS'): (2700, 4400),
            ('GIG', 'CDG'): (2700, 4400),
            ('GIG', 'MAD'): (2500, 4100),
            ('GIG', 'LHR'): (2800, 4500),
            ('BSB', 'MIA'): (2400, 4000),
            ('BSB', 'LIS'): (2900, 4600),
            ('BSB', 'MAD'): (2600, 4200),
            ('BSB', 'CDG'): (2700, 4400),
            ('CWB', 'MIA'): (2400, 4000),
            ('CWB', 'LIS'): (2900, 4600),
            ('CWB', 'MAD'): (2600, 4200),
            ('CWB', 'EZE'): (850, 1550),
            ('MAO', 'MIA'): (2200, 3800),
            ('MAO', 'MAD'): (2800, 4500),
            ('MAO', 'LIS'): (2900, 4600),
            ('SSA', 'LIS'): (2600, 4200),
            ('SSA', 'MAD'): (2500, 4100),
            ('SSA', 'MIA'): (2300, 3900),
            ('FOR', 'LIS'): (2600, 4200),
            ('FOR', 'MIA'): (2200, 3800),
            ('FOR', 'MAD'): (2500, 4100),
            ('REC', 'LIS'): (2500, 4100),
            ('REC', 'MIA'): (2200, 3800),
            ('POA', 'MIA'): (2400, 4000),
            ('POA', 'EZE'): (800, 1500),
            ('FLN', 'MIA'): (2400, 4000),
            ('FLN', 'EZE'): (850, 1550),
        }
        
        # Companhias aéreas reais por rota
        self.airlines = {
            'LIS': ['TAP Air Portugal', 'LATAM', 'Azul'],
            'MIA': ['LATAM', 'American Airlines', 'Gol'],
            'MCO': ['LATAM', 'American Airlines', 'Gol'],
            'JFK': ['LATAM', 'American Airlines', 'Delta'],
            'CDG': ['Air France', 'LATAM', 'Air Europa'],
            'MAD': ['Iberia', 'LATAM', 'Air Europa'],
            'BCN': ['LATAM', 'Iberia', 'Vueling'],
            'LHR': ['British Airways', 'LATAM', 'Virgin Atlantic'],
            'FCO': ['ITA Airways', 'LATAM', 'Azul'],
            'AMS': ['KLM', 'LATAM', 'Air Europa'],
            'EZE': ['Aerolineas Argentinas', 'LATAM', 'Gol'],
            'SCL': ['LATAM', 'Sky Airline', 'Gol'],
        }

    def get_place_id(self, airport_code):
        """Busca o ID interno do aeroporto na API"""
        if not self.client:
            return None
            
        url = f"{self.base_url}/flights/searchAirport"
        querystring = {"query": airport_code}
        
        try:
            response = requests.get(url, headers=self.headers, params=querystring, timeout=10)
            if response.status_code == 200:
                data = response.json()
                places = data.get("places", [])
                
                if not places and isinstance(data, list):
                    places = data
                
                for place in places:
                    if place.get("iata", "").upper() == airport_code.upper():
                        return {
                            "skyId": place.get("skyId"),
                            "entityId": place.get("entityId")
                        }
                
                if places:
                    return {
                        "skyId": places[0].get("skyId"),
                        "entityId": places[0].get("entityId")
                    }
            return None
        except Exception as e:
            print(f"   ⚠️ Erro ao buscar ID: {e}")
            return None

    def search_flights_api(self, origin_iata, destination_iata, date_from):
        """Tenta buscar voos reais na API"""
        if not self.client:
            return None

        # Buscar IDs
        origin_data = self.get_place_id(origin_iata)
        dest_data = self.get_place_id(destination_iata)

        if not origin_data or not dest_data:
            print(f"   ⚠️ IDs não encontrados")
            return None

        # Buscar voos
        url = f"{self.base_url}/flights/searchFlights"
        
        querystring = {
            "originSkyId": origin_data.get("skyId", ""),
            "originEntityId": origin_data.get("entityId", ""),
            "destinationSkyId": dest_data.get("skyId", ""),
            "destinationEntityId": dest_data.get("entityId", ""),
            "date": date_from,
            "cabinClass": "economy",
            "adults": "1",
            "currency": "BRL"
        }

        try:
            response = requests.get(url, headers=self.headers, params=querystring, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Tentar diferentes estruturas de resposta
                itineraries = []
                if isinstance(data, dict):
                    itineraries = data.get("data", {}).get("itineraries", [])
                    if not itineraries:
                        itineraries = data.get("itineraries", [])
                elif isinstance(data, list):
                    itineraries = data
                
                if itineraries:
                    best = itineraries[0]
                    price_info = best.get("price", {})
                    price = price_info.get("raw") or price_info.get("amount")
                    
                    airline = "Várias"
                    legs = best.get("legs", [])
                    if legs:
                        carriers = legs[0].get("carriers", [])
                        if carriers:
                            airline = carriers[0].get("name", "Desconhecida")
                    
                    if price and price > 100:
                        return {'price': float(price), 'airline': airline, 'currency': 'BRL'}
                
                print(f"   ⚠️ API retornou, mas sem itinerários")
                return None
            else:
                print(f"   ⚠️ API retornou status {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ⚠️ Erro na requisição: {e}")
            return None

    def get_fallback_price(self, origin, destination):
        """Gera preço realista baseado em dados de referência"""
        key = (origin, destination)
        
        if key in self.reference_prices:
            min_price, max_price = self.reference_prices[key]
            # Gera preço aleatório dentro da faixa com variação de ±10%
            base_price = random.uniform(min_price, max_price)
            variation = random.uniform(0.9, 1.1)
            price = base_price * variation
            
            # Arredonda para centena
            price = round(price / 100) * 100
            
            # Escolhe companhia aleatória
            airline_list = self.airlines.get(destination, ['LATAM', 'Gol', 'Azul'])
            airline = random.choice(airline_list)
            
            print(f"   📊 Preço simulado realista: R$ {price:.2f} ({airline})")
            return {
                'price': price,
                'airline': airline,
                'currency': 'BRL'
            }
        
        # Preço padrão se não encontrar na tabela
        default_price = random.uniform(2000, 4000)
        print(f"   📊 Preço simulado padrão: R$ {default_price:.2f}")
        return {
            'price': default_price,
            'airline': 'Companhia Internacional',
            'currency': 'BRL'
        }

    def generate_booking_links(self, origin, destination, date_from, date_to):
        """Gera links de busca para compra"""
        
        # Google Flights
        google_url = (
            f"https://www.google.com/travel/flights?"
            f"hl=pt-BR"
            f"&gl=br"
            f"&curr=BRL"
            f"&tt=d"
            f"&sd={date_from.replace('-', '/')}"
            f"&ed={date_to.replace('-', '/')}"
            f"&d={origin}"
            f"&r={destination}"
        )
        
        # Skyscanner
        skyscanner_url = (
            f"https://www.skyscanner.com.br/transport/flights/"
            f"{origin.lower()}/{destination.lower()}/"
            f"{date_from.replace('-', '/')}/"
            f"{date_to.replace('-', '/')}/"
            f"?adults=1&children=0&adultsv2=1&childrenv2=&"
            f"infants=0&cabinclass=economy&"
            f"rtn=1&preferdirects=false&"
            f"outboundaltsenabled=false&"
            f"inboundaltsenabled=false&ref=home"
        )
        
        return {
            'google_flights': google_url,
            'skyscanner': skyscanner_url
        }

    def get_flight_data(self, origin: str, destination: str, date_from: str, date_to: str = None):
        """
        Método principal: tenta API real, fallback para simulado
        """
        print(f"   🔍 Buscando: {origin} → {destination} para {date_from}")
        
        # Tenta API real primeiro
        flight_data = self.search_flights_api(origin, destination, date_from)
        
        if flight_data:
            print(f"   ✅ Dados REAIS obtidos!")
            return flight_data
        
        # Fallback para dados simulados realistas
        print(f"   🔄 Usando dados simulados (API sem dados)")
        return self.get_fallback_price(origin, destination)
