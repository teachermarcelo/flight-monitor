import os
import requests

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

    def get_place_id(self, query):
        """Busca o ID interno do aeroporto (ex: GRU -> 95673462)"""
        url = f"{self.base_url}/flights/searchAirport"
        querystring = {"query": query}
        
        try:
            response = requests.get(url, headers=self.headers, params=querystring)
            if response.status_code == 200:
                data = response.json()
                # A API geralmente retorna uma lista de lugares
                # Pegamos o primeiro resultado que tenha o IATA code igual ao nosso
                places = data.get("places", []) # Tenta acessar chave 'places'
                
                # Se não tiver 'places', pode ser que a resposta seja a lista direta
                if not places and isinstance(data, list):
                    places = data

                for place in places:
                    if place.get("iata") == query:
                        return {
                            "skyId": place.get("skyId"),
                            "entityId": place.get("entityId")
                        }
                
                # Se não achou pelo IATA exato, pega o primeiro da lista
                if places:
                    return {
                        "skyId": places[0].get("skyId"),
                        "entityId": places[0].get("entityId")
                    }
                    
            return None
        except Exception as e:
            print(f"❌ Erro ao buscar ID de {query}: {e}")
            return None

    def get_flight_data(self, origin_iata, destination_iata, date_from, date_to=None):
        """Busca voos usando os IDs internos"""
        
        if not self.client:
            return None

        # 1. Pegar IDs de Origem e Destino
        print(f"   🔍 Buscando IDs para {origin_iata} e {destination_iata}...")
        origin_data = self.get_place_id(origin_iata)
        dest_data = self.get_place_id(destination_iata)

        if not origin_data or not dest_data:
            print(f"   ❌ Não conseguiu encontrar IDs válidos para a rota.")
            return None

        # 2. Buscar Voos com os IDs
        url = f"{self.base_url}/flights/searchFlights"
        
        querystring = {
            "originSkyId": origin_data["skyId"],
            "originEntityId": origin_data["entityId"],
            "destinationSkyId": dest_data["skyId"],
            "destinationEntityId": dest_data["entityId"],
            "date": date_from,       # A API exige 'date'
            "cabinClass": "economy",
            "adults": "1",
            "currency": "BRL"
        }
        
        # Se for ida e volta (opcional, a API pode suportar)
        if date_to:
            querystring["returnDate"] = date_to

        try:
            response = requests.get(url, headers=self.headers, params=querystring)
            
            if response.status_code == 200:
                data = response.json()
                
                # A estrutura da resposta varia muito. 
                # Geralmente é data['data']['itineraries'] ou data['itineraries']
                itineraries = data.get("data", {}).get("itineraries", [])
                if not itineraries:
                    itineraries = data.get("itineraries", [])

                if itineraries:
                    best_offer = itineraries[0]
                    # O preço geralmente está em best_offer['price']['raw'] ou similar
                    price_obj = best_offer.get("price", {})
                    price = price_obj.get("raw") or price_obj.get("amount")
                    
                    # Companhia aérea
                    legs = best_offer.get("legs", [])
                    airline = "Várias"
                    if legs:
                        carriers = legs[0].get("carriers", [])
                        if carriers:
                            airline = carriers[0].get("name", "Desconhecida")

                    if price:
                        print(f"   ✅ Preço encontrado: R$ {price:.2f} ({airline})")
                        return {
                            'price': float(price),
                            'airline': airline,
                            'currency': 'BRL'
                        }
                    else:
                        print(f"   ⚠️ Preço não encontrado no JSON.")
                        return None
                else:
                    print(f"   ⚠️ Nenhum voo encontrado na resposta.")
                    return None
            else:
                print(f"   ❌ Erro na API Voos (Status {response.status_code}): {response.text[:100]}")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro de conexão: {e}")
            return None
