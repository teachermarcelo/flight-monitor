import os
import requests
from dotenv import load_dotenv

load_dotenv()

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> int:
        """Envia mensagem para o Telegram"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            return response.json()['result']['message_id']
        return None
    
    def send_flight_alert(self, origin: str, destination: str, 
                          price: float, airline: str, 
                          departure: str, old_price: float = None):
        """Envia alerta de promoção formatado"""
        # Calcula desconto se tiver preço anterior
        discount = ""
        if old_price:
            percent = ((old_price - price) / old_price) * 100
            discount = f"\n💸 <b>QUEDA DE {percent:.0f}%!</b>\nDe: R$ {old_price:,.2f}"
        
        message = f"""
🚨 <b>PROMOÇÃO ENCONTRADA!</b> 🚨

✈️ <b>Rota:</b> {origin} → {destination}
💰 <b>Preço:</b> R$ {price:,.2f}
🏢 <b>Companhia:</b> {airline}
📅 <b>Saída:</b> {departure}
{discount}

🔗 <a href="https://www.google.com/flights">Buscar no Google Flights</a>

⚡ <i>Corre que pode acabar!</i>
        """
        
        return self.send_message(message.strip())
