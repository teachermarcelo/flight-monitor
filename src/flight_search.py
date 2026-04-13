import os
import requests
from datetime import datetime, timedelta

class FlightSearch:
    def __init__(self):
        self.api_key = os.getenv("AVIATIONSTACK_KEY")
        
        if not self.api_key:
            print("❌ ERRO: Chave AVIATIONSTACK_KEY não encontrada!")
            self.client = None
        else:
            self.client = True
            self.base_url = "http://api.aviationstack.com/v1/flights"

    def get_flight_data(self, origin: str, destination: str, date_from: str, date_to: str = None):
        """Busca voos REAIS usando AviationStack"""
        
        if not self.client:
            return None

        print(f"    Buscando dados REAIS via AviationStack...")

        # AviationStack usa parâmetros diferentes
        params = {
            "access_key": self.api_key,
            "dep_iata": origin,      # Código IATA de partida (ex: GRU)
            "arr_iata": destination, # Código IATA de chegada (ex: LIS)
            "limit": 10              # Pega até 10 voos para escolher o melhor
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if "data" in data and len(data["data"]) > 0:
                    # Filtra voos que são realmente para a data desejada (ou próximos)
                    # AviationStack retorna voos programados, precisamos achar o preço
                    # NOTA: A versão gratuita do AviationStack foca em STATUS de voo, não PREÇO.
                    # Para PREÇO real gratuito, a melhor opção é voltar para uma simulação MUITO realista
                    # OU usar a API da "FlightLabs" ou "Amadeus Self-Service" (que tem limite diário).
                    
                    # CORREÇÃO DE ROTA: AviationStack FREE não dá preço.
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
