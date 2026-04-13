import os
from supabase import create_client, Client
from datetime import datetime, timedelta

class TarifIntelligence:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    def get_route_average(self, origin, destination):
        """Busca a média histórica da rota"""
        try:
            response = self.supabase.table("route_averages").select("*").eq("origin", origin).eq("destination", destination).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"   ⚠️ Erro ao buscar média: {e}")
            return None

    def update_route_average(self, origin, destination, new_price):
        """Atualiza a média histórica com novo preço (média móvel simples)"""
        try:
            current_avg = self.get_route_average(origin, destination)
            
            if current_avg:
                # Calcula nova média (simples: média entre antiga e nova)
                # Em produção, usaríamos uma média ponderada ou janela de tempo
                new_avg = (current_avg['avg_price'] + new_price) / 2
                
                # Atualiza min/max se necessário
                new_min = min(current_avg['min_price'], new_price)
                new_max = max(current_avg['max_price'], new_price)
                
                self.supabase.table("route_averages").update({
                    "avg_price": new_avg,
                    "min_price": new_min,
                    "max_price": new_max,
                    "last_updated": datetime.now().isoformat()
                }).eq("origin", origin).eq("destination", destination).execute()
            else:
                # Se não existe, cria nova entrada
                self.supabase.table("route_averages").insert({
                    "origin": origin,
                    "destination": destination,
                    "avg_price": new_price,
                    "min_price": new_price,
                    "max_price": new_price
                }).execute()
                
        except Exception as e:
            print(f"   ️ Erro ao atualizar média: {e}")

    def analyze_tarif(self, origin, destination, current_price):
        """Analisa se o preço atual é uma oferta/error fare"""
        
        avg_data = self.get_route_average(origin, destination)
        
        if not avg_data:
            # Sem histórico, considera normal
            return {
                "is_offer": False,
                "discount_percent": 0,
                "classification": "SEM_HISTORICO",
                "message": "Sem histórico suficiente para análise."
            }
        
        avg_price = avg_data['avg_price']
        min_price = avg_data['min_price']
        
        # Calcula desconto em relação à média
        discount_amount = avg_price - current_price
        discount_percent = (discount_amount / avg_price) * 100 if avg_price > 0 else 0
        
        # Classificação
        classification = "NORMAL"
        is_offer = False
        message = ""
        
        if current_price <= min_price * 0.9: 
            # Preço 10% abaixo do mínimo histórico registrado -> ERRO DE TARIFA PROVÁVEL
            classification = "ERRO_TARIFA_PROVAVEL"
            is_offer = True
            message = f" ALERTA MÁXIMO! Preço {discount_percent:.1f}% abaixo da média. Possível erro de tarifa!"
        elif discount_percent >= 40:
            classification = "OFERTA_EXCELENTE"
            is_offer = True
            message = f"🔥 OFERTA EXCELENTE! {discount_percent:.1f} de desconto em relação à média."
        elif discount_percent >= 25:
            classification = "OFERTA_BOA"
            is_offer = True
            message = f"✅ Boa oferta! {discount_percent:.1f} de desconto."
        elif discount_percent >= 15:
            classification = "OFERTA_LEVE"
            is_offer = True
            message = f"👍 Oferta leve. {discount_percent:.1f} de desconto."
        else:
            message = "Preço dentro da normalidade."
            
        # Atualiza histórico com este novo preço
        self.update_route_average(origin, destination, current_price)
        
        return {
            "is_offer": is_offer,
            "discount_percent": round(discount_percent, 1),
            "classification": classification,
            "average_price": avg_price,
            "message": message
        }
