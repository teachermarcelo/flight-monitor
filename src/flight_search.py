import os
import requests
from datetime import datetime, timedelta

class FlightSearch:
    def __init__(self):
        # RapidAPI Configuration
        self.api_key = os.getenv("RAPIDAPI_KEY")
        self.api_host = os.getenv("RAPIDAPI_HOST")
        
        if not self.api_key or not self.api_host:
            print("❌ Credenciais da RapidAPI não encontradas!")
            self.client = None
        else:
            self.client = True # Apenas para indicar que temos as chaves
            self.headers = {
                "X-RapidAPI-Key": self.api_key,
                "X-RapidAPI-Host": self.api_host
            }
            self.base_url = f"https://{self.api_host}"

    def get_flight_data(self, origin: str, destination: str, date_from: str, date_to: str = None):
        """Busca voos na API do Skyscanner via RapidAPI"""
        
        if not self.client:
            return None

        # Endpoint específico para busca de voos
        url = f"{self.base_url}/flights/searchFlights"
        
        # Parâmetros da busca
        querystring = {
            "fromId": origin,          # ex: GRU
            "toId": destination,       # ex: LIS
            "departDate": date_from,   # ex: 2026-05-01
            "adults": "1",
            "currency": "BRL",
            "cabinClass": "economy"
        }
        
        if date_to:
            querystring["returnDate"] = date_to

        try:
            response = requests.get(url, headers=self.headers, params=querystring)
            
            if response.status_code == 200:
                data = response.json()
                
                # ATENÇÃO: A estrutura do JSON varia conforme a API.
                # Geralmente vem algo como data['data']['itineraries'] ou similar.
                # Vamos tentar acessar o primeiro preço encontrado.
                
                # Tenta acessar o campo de preço (ajuste conforme o JSON real da API)
                # Muitas APIs retornam uma lista de 'itineraries' ou 'offers'
                itineraries = data.get("data", {}).get("itineraries", [])
                
                if itineraries:
                    best_offer = itineraries[0]
                    price = best_offer.get("price", {}).get("raw", 0) # Ou 'total'
                    airline = best_offer.get("legs", [{}])[0].get("carriers", ["Desconhecida"])[0]
                    
                    # Se o preço for muito baixo ou zero, ignora (erro de API)
                    if price and price > 100:
                        print(f"✅ Preço encontrado: R$ {price:.2f} ({airline})")
                        return {
                            'price': float(price),
                            'airline': airline,
                            'currency': 'BRL'
                        }
                    else:
                        print(f"⚠️ Preço inválido ({price}) para {origin} → {destination}")
                        return None
                else:
                    print(f"⚠️ Nenhum voo encontrado para {origin} → {destination}")
                    return None
            else:
                print(f"❌ Erro na API (Status {response.status_code}): {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
            return None
