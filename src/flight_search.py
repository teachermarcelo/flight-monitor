import os
import requests
import random
from datetime import datetime, timedelta

class FlightSearch:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        
        if not self.api_key:
            print("❌ ERRO: SERPAPI_KEY não encontrada!")
            self.client = None
        else:
            self.client = True
            self.base_url = "https://serpapi.com/search.json"
        
        # Dados de fallback realistas
        self.fallback_prices = {
            ('GRU', 'LIS'): {'min': 2800, 'max': 5500, 'avg': 3800},
            ('GRU', 'MIA'): {'min': 2200, 'max': 4500, 'avg': 3200},
            ('GRU', 'MCO'): {'min': 2300, 'max': 4600, 'avg': 3300},
            ('GRU', 'JFK'): {'min': 2500, 'max': 5000, 'avg': 3500},
            ('GRU', 'CDG'): {'min': 2600, 'max': 5200, 'avg': 3600},
            ('GRU', 'MAD'): {'min': 2400, 'max': 4800, 'avg': 3400},
            ('GRU', 'EZE'): {'min': 800, 'max': 2000, 'avg': 1200},
            ('CWB', 'MIA'): {'min': 2400, 'max': 4800, 'avg': 3400},
            ('CWB', 'LIS'): {'min': 2900, 'max': 5700, 'avg': 4000},
            ('CWB', 'EZE'): {'min': 850, 'max': 2100, 'avg': 1300},
            # ... adicione mais rotas conforme necessário
        }
        
        self.airlines = {
            'LIS': ['TAP Air Portugal', 'LATAM Airlines', 'Azul'],
            'MIA': ['LATAM Airlines', 'American Airlines', 'Gol'],
            'MCO': ['LATAM Airlines', 'American Airlines', 'Gol'],
            'JFK': ['LATAM Airlines', 'American Airlines', 'Delta'],
            'CDG': ['Air France', 'LATAM Airlines', 'Air Europa'],
            'MAD': ['Iberia', 'LATAM Airlines', 'Air Europa'],
            'EZE': ['Aerolineas Argentinas', 'LATAM Airlines', 'Gol'],
        }

    def get_flight_data(self, origin: str, destination: str, date_from: str, date_to: str = None):
        """Busca voos REAIS ou usa fallback inteligente"""
        
        # Primeiro tenta API real
        if self.client:
            print(f"   🔍 Tentando buscar no Google Voos (SerpApi)...")
            
            params = {
                "engine": "google_flights",
                "hl": "pt-BR",
                "gl": "br", 
                "curr": "BRL",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": date_from,
                "return_date": date_to if date_to else "",
                "api_key": self.api_key
            }

            try:
                response = requests.get(self.base_url, params=params, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "flights" in data and len(data["flights"]) > 0:
                        best_flight = data["flights"][0]
                        price_str = best_flight.get("price", "0")
                        price_clean = price_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
                        
                        try:
                            price = float(price_clean)
                            airlines_list = best_flight.get("airlines", [])
                            airline = airlines_list[0] if isinstance(airlines_list, list) and airlines_list else "Várias Companhias"
                            
                            print(f"   ✅ DADO REAL ENCONTRADO: R$ {price:.2f} ({airline})")
                            return {
                                'price': price,
                                'airline': airline,
                                'currency': 'BRL',
                                'source': 'Google Flights (SerpApi)'
                            }
                        except ValueError:
                            pass
                
                print(f"   ⚠️ API não retornou resultados válidos")
                
            except Exception as e:
                print(f"   ⚠️ Erro na API: {e}")
        
        # Fallback para dados simulados realistas
        print(f"   🔄 Usando dados simulados realistas...")
        return self._get_fallback_price(origin, destination)

    def _get_fallback_price(self, origin, destination):
        """Gera preço realista baseado em dados de mercado"""
        key = (origin, destination)
        
        if key in self.fallback_prices:
            price_data = self.fallback_prices[key]
            # Gera preço aleatório dentro da faixa com variação diária
            base_price = random.uniform(price_data['min'], price_data['max'])
            variation = random.uniform(0.85, 1.15)  # Variação de ±15%
            price = base_price * variation
            
            # Arredonda para centena
            price = round(price / 100) * 100
            
            # Escolhe companhia aleatória
            airline_list = self.airlines.get(destination, ['LATAM', 'Gol', 'Azul'])
            airline = random.choice(airline_list)
            
            print(f"   📊 Preço simulado: R$ {price:.2f} ({airline})")
            return {
                'price': price,
                'airline': airline,
                'currency': 'BRL',
                'source': 'Simulação Inteligente'
            }
        
        # Preço padrão se não encontrar na tabela
        default_price = random.uniform(2000, 4000)
        print(f"   📊 Preço padrão simulado: R$ {default_price:.2f}")
        return {
            'price': default_price,
            'airline': 'Companhia Internacional',
            'currency': 'BRL',
            'source': 'Simulação Padrão'
        }
