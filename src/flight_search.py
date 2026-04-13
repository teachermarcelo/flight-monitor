import os
import requests
from datetime import datetime

class FlightSearch:
    def __init__(self):
        # Pega a chave da SerpApi das variáveis de ambiente do GitHub
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
        Retorna dicionário com preço, companhia e moeda.
        """
        
        if not self.client:
            return None

        print(f"   🔍 Conectando ao Google Voos via SerpApi...")

        # Configuração dos parâmetros da busca
        params = {
            "engine": "google_flights",
            "hl": "pt-BR",          # Idioma Português
            "gl": "br",             # Região Brasil
            "curr": "BRL",          # Moeda Real
            "departure_id": origin, # Código IATA (ex: GRU)
            "arrival_id": destination, # Código IATA (ex: LIS)
            "outbound_date": date_from,
            "return_date": date_to if date_to else "",
            "api_key": self.api_key
        }

        try:
            # Faz a requisição à SerpApi
            response = requests.get(self.base_url, params=params, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verifica se a API retornou voos
                if "flights" in data and len(data["flights"]) > 0:
                    # Pega o primeiro voo (geralmente o mais barato ou recomendado)
                    best_flight = data["flights"][0]
                    
                    # Extração e limpeza do preço
                    # O Google retorna como string: "R$ 3.500" ou "R$3.500,00"
                    price_raw = best_flight.get("price", "0")
                    
                    # Limpeza: Remove 'R$', espaços, troca vírgula por ponto
                    price_clean = price_raw.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    
                    try:
                        price = float(price_clean)
                    except ValueError:
                        print(f"   ⚠️ Erro ao converter preço '{price_raw}' para número.")
                        return None

                    # Extração da companhia aérea
                    airlines_list = best_flight.get("airlines", [])
                    airline = airlines_list[0] if isinstance(airlines_list, list) and airlines_list else "Várias Companhias"
                    
                    print(f"   ✅ DADO REAL ENCONTRADO: R$ {price:.2f} | Cia: {airline}")
                    
                    return {
                        'price': price,
                        'airline': airline,
                        'currency': 'BRL',
                        'source': 'Google Flights (SerpApi)',
                        'flight_details': best_flight.get('flight_number', 'N/A')
                    }
                else:
                    print(f"   ️ Nenhum voo encontrado no Google para {origin} → {destination} nestas datas.")
                    return None
            else:
                print(f"   ❌ Erro na API SerpApi (Status {response.status_code}). Verifique sua chave ou créditos.")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro de conexão com SerpApi: {e}")
            return None            "outbound_date": date_from,
            "return_date": date_to if date_to else "",
            "api_key": self.api_key
        }

        try:
            # Faz a requisição à SerpApi
            response = requests.get(self.base_url, params=params, timeout=25)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verifica se a API retornou voos
                if "flights" in data and len(data["flights"]) > 0:
                    # Pega o primeiro voo (geralmente o mais barato ou recomendado)
                    best_flight = data["flights"][0]
                    
                    # Extração e limpeza do preço
                    # O Google retorna como string: "R$ 3.500" ou "R$3.500,00"
                    price_raw = best_flight.get("price", "0")
                    
                    # Limpeza: Remove 'R$', espaços, troca vírgula por ponto
                    price_clean = price_raw.replace("R$", "").replace(" ", "").replace(".", "").replace(",", ".")
                    
                    try:
                        price = float(price_clean)
                    except ValueError:
                        print(f"   ️ Erro ao converter preço '{price_raw}' para número.")
                        return None

                    # Extração da companhia aérea
                    airlines_list = best_flight.get("airlines", [])
                    airline = airlines_list[0] if isinstance(airlines_list, list) and airlines_list else "Várias Companhias"
                    
                    print(f"   ✅ DADO REAL ENCONTRADO: R$ {price:.2f} | Cia: {airline}")
                    
                    return {
                        'price': price,
                        'airline': airline,
                        'currency': 'BRL',
                        'source': 'Google Flights (SerpApi)',
                        'flight_details': best_flight.get('flight_number', 'N/A')
                    }
                else:
                    print(f"   ⚠️ Nenhum voo encontrado no Google para {origin} → {destination} nestas datas.")
                    return None
            else:
                print(f"   ❌ Erro na API SerpApi (Status {response.status_code}). Verifique sua chave ou créditos.")
                return None
                
        except Exception as e:
            print(f"   ❌ Erro de conexão com SerpApi: {e}")
            return None                    # CORREÇÃO DE ROTA: AviationStack FREE não dá preço.
                    # Vamos usar a lógica de "Simulação Híbrida Inteligente" que é a única forma gratuita estável de ter preços variados.
                    # Mas para atender seu pedido de "Precisão", vamos tentar a Amadeus Self-Service que é a única com preço real grátis.
                    
                    # Se quiser continuar tentando APIs de preço real, avise.
                    # Por enquanto, vou retornar None para forçar o fallback ou mudarmos de estratégia.
                    print(f"   ⚠️ AviationStack Free não fornece preços em tempo real, apenas status.")
                    return None
                else:
                    print(f"   ⚠️ Nenhum voo encontrado na AviationStack.")
                    return None
            else:
                print(f"   ❌ Erro AviationStack: {response.text}")
                return None
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            return None
