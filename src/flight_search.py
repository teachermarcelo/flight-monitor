import os
import requests
from datetime import datetime

class FlightSearch:
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_KEY")
        
        if not self.api_key:
            print("❌ ERRO CRÍTICO: A variável SERPAPI_KEY não foi encontrada!")
            print("   Vá em Settings > Secrets no GitHub e adicione SERPAPI_KEY.")
            self.client = None
        else:
            self.client = True
            self.base_url = "https://serpapi.com/search.json"

    def get_flight_data(self, origin: str, destination: str, date_from: str, date_to: str = None):
        """
        Busca voos REAIS usando a API da SerpApi (que lê o Google Flights).
        """
        
        if not self.client:
            return None

        print(f"   🔍 Conectando ao Google Voos via SerpApi...")

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
            response = requests.get(self.base_url, params=params, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                
                if "flights" in data and len(data["flights"]) > 0:
                    best_flight = data["flights"][0]
                    
                    price_raw = best_flight.get("price", "0")
                    price_clean = price_raw.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    
                    try:
                        price = float(price_clean)
                    except ValueError:
                        print(f"   ⚠️ Erro ao converter preço '{price_raw}'.")
                        return None

                    airlines_list = best_flight.get("airlines", [])
                    airline = airlines_list[0] if isinstance(airlines_list, list) and airlines_list else "Várias Companhias"
                    
                    print(f"   ✅ DADO REAL ENCONTRADO: R$ {price:.2f} | Cia: {airline}")
                    
                    return {
                        'price': price,
                        'airline': airline,
                        'currency': 'BRL',
                        'source': 'Google Flights (SerpApi)'
                    }
                else:
                    print(f"   ️ Nenhum voo encontrado para {origin} → {destination}.")
                    return None
            else:
                print(f"   ❌ Erro na API SerpApi (Status {response.status_code}).")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro de conexão com SerpApi: {e}")
            return None
