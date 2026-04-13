import os
import requests
from datetime import datetime, timedelta

class FlightSearch:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        
        if not self.api_key:
            print("❌ ERRO: Chave SERPAPI_KEY não encontrada nos secrets do GitHub!")
            self.client = None
        else:
            self.client = True
            self.base_url = "https://serpapi.com/search.json"

    def get_flight_data(self, origin: str, destination: str, date_from: str, date_to: str = None):
        """Busca voos REAIS usando SerpApi (Google Flights)"""
        
        if not self.client:
            return None

        print(f"   🔍 Buscando dados REAIS no Google Voos via SerpApi...")

        # Parâmetros da requisição para a SerpApi
        params = {
            "engine": "google_flights",
            "hl": "pt-BR",       # Idioma Português
            "gl": "br",          # Região Brasil
            "curr": "BRL",       # Moeda Real
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
                
                # Verifica se há resultados de voos
                if "flights" in data and len(data["flights"]) > 0:
                    best_flight = data["flights"][0] # Pega o primeiro (geralmente o mais barato/relevante)
                    
                    price_str = best_flight.get("price", "0")
                    # Remove 'R$' e espaços, converte para float
                    price_clean = price_str.replace("R$", "").replace(".", "").replace(",", ".").strip()
                    
                    try:
                        price = float(price_clean)
                    except ValueError:
                        print(f"   ⚠️ Erro ao converter preço: {price_str}")
                        return None

                    airline = best_flight.get("airlines", ["Desconhecida"])[0] if isinstance(best_flight.get("airlines"), list) else best_flight.get("airlines", "Desconhecida")
                    
                    print(f"   ✅ DADO REAL ENCONTRADO: R$ {price:.2f} ({airline})")
                    
                    return {
                        'price': price,
                        'airline': airline,
                        'currency': 'BRL',
                        'source': 'Google Flights (SerpApi)'
                    }
                else:
                    print(f"   ⚠️ Nenhum voo encontrado no Google para {origin} → {destination}")
                    return None
            else:
                print(f"   ❌ Erro na API SerpApi (Status {response.status_code}): {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro de conexão com SerpApi: {e}")
            return None
