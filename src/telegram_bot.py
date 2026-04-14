# -*- coding: utf-8 -*-
import os
import requests
from datetime import datetime

class TelegramAlertBot:
       def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # DEBUG: Mostra o que o sistema está lendo (oculta parte do token por segurança)
        token_preview = f"{self.bot_token[:10]}..." if self.bot_token else "NENHUM"
        print(f" DEBUG TELEGRAM: Token = {token_preview} | Chat ID = {self.chat_id}")
        
        if not self.bot_token or not self.chat_id:
            print("⚠️ Credenciais do Telegram não configuradas ou vazias!")
            self.enabled = False
        else:
            print("✅ Credenciais do Telegram carregadas com sucesso!")
            self.enabled = True
            self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    def send_alert(self, route_origin, route_dest, current_price, avg_price, discount_percent, classification, airline, google_link):
        """Envia alerta formatado profissional para Telegram"""
        
        if not self.enabled:
            print("   ⚠️ Bot do Telegram desativado")
            return

        # Emoji baseado na classificação
        emojis = {
            'ERRO_TARIFA_PROVAVEL': '🚨',
            'OFERTA_EXCELENTE': '', 
            'OFERTA_BOA': '✅',
            'OFERTA_LEVE': '👍'
        }
        emoji = emojis.get(classification, '✈️')

        # Calcula economia
        savings = avg_price - current_price
        
        message = f"""
{emoji} *ALERTA DE PASSAGENS!* {emoji}

 *{route_origin} → {route_dest}*
💰 *Preço Atual:* R$ {current_price:,.2f}
 *Preço Médio:* R$ {avg_price:,.2f}
🎯 *Economia:* R$ {savings:,.2f} ({discount_percent:.1f}% OFF)

✈️ *Companhia:* {airline}
📅 *Data da Busca:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

 *Link para Compra:*
{google_link}

 *Classificação:* {classification}
"""

        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Alerta enviado para Telegram!")
            else:
                print(f"   ❌ Erro ao enviar Telegram: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Erro de conexão com Telegram: {e}")
