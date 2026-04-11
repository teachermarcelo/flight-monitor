import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
import requests

load_dotenv()

class ReadmeGenerator:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPOSITORY")
    
    def get_stats(self):
        """Pega estatísticas gerais"""
        routes = self.supabase.table("monitored_routes").select("*").execute()
        total_routes = len([r for r in routes.data if r.get('active', False)])
        
        prices = self.supabase.table("price_history").select("*").execute()
        total_prices = len(prices.data)
        
        alerts = self.supabase.table("alerts_sent").select("*").execute()
        total_alerts = len(alerts.data)
        
        return {
            'total_routes': total_routes,
            'total_prices': total_prices,
            'total_alerts': total_alerts
        }
    
    def generate_markdown(self):
        """Gera o conteúdo do README"""
        stats = self.get_stats()
        
        md = f"""# ✈️ Flight Monitor Dashboard

Última atualização: **{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}** (UTC)

---

## 📊 Estatísticas Gerais

| Métrica | Valor |
|---------|-------|
| 🎯 Rotas Monitoradas | {stats['total_routes']} |
| 💰 Preços Rastreados | {stats['total_prices']} |
| 🚨 Alertas Enviados | {stats['total_alerts']} |

---

## 🤖 Como Funciona

- **Atualização automática**: A cada 6 horas via GitHub Actions
- **Alertas**: Criados automaticamente quando o preço cai 15%
- **Dados**: Armazenados no Supabase

---

*Atualizado automaticamente por Flight Monitor*
"""
        
        return md
    
    def update_readme(self):
        """Atualiza o README no GitHub"""
        content = self.generate_markdown()
        
        url = f"https://api.github.com/repos/{self.repo}/contents/README.md"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        sha = response.json()['sha'] if response.status_code == 200 else None
        
        data = {
            "message": "🤖 Update: Dashboard automático",
            "content": content,
            "sha": sha
        }
        
        response = requests.put(url, headers=headers, json=data)
        
        if response.status_code in [200, 201]:
            print("✅ README atualizado com sucesso!")
        else:
            print(f"❌ Erro: {response.text}")

if __name__ == "__main__":
    generator = ReadmeGenerator()
    generator.update_readme()
