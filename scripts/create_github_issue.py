import os
from datetime import datetime, timedelta
from supabase import create_client
from github import Github
from dotenv import load_dotenv

load_dotenv()

class GitHubIssueCreator:
    def __init__(self):
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        self.github = Github(os.getenv("GITHUB_TOKEN"))
        self.repo = self.github.get_repo(os.getenv("GITHUB_REPOSITORY"))
    
    def get_new_alerts(self):
        """Pega alertas das últimas 2 horas"""
        two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
        
        alerts = self.supabase.table("alerts_sent")\
            .select("*, route:monitored_routes(origin, destination, max_price)")\
            .gte("sent_at", two_hours_ago)\
            .execute()
        
        return alerts.data
    
    def create_issue(self, alert):
        """Cria uma issue no GitHub"""
        route = alert.get('route', {})
        
        title = f"🔥 PROMOÇÃO: {route.get('origin')} → {route.get('destination')} por R$ {alert['price']:,.2f}"
        
        body = f"""
## Detalhes da Promoção

**Rota:** {route.get('origin')} → {route.get('destination')}  
**Preço:** R$ {alert['price']:,.2f}  
**Preço Máximo:** R$ {route.get('max_price', 'N/A'):,.2f}  
**Data/Hora:** {alert['sent_at']}  

### Ação Recomendada
✅ Comprar imediatamente se estiver dentro do orçamento!

---
*Issue criada automaticamente pelo Flight Monitor*
"""
        
        issue = self.repo.create_issue(
            title=title,
            body=body,
            labels=["promoção", "alerta"]
        )
        
        return issue.number
    
    def run(self):
        """Executa a criação de issues"""
        alerts = self.get_new_alerts()
        
        print(f"Encontrados {len(alerts)} alertas recentes")
        
        for alert in alerts:
            try:
                issue_number = self.create_issue(alert)
                print(f"✅ Issue #{issue_number} criada")
            except Exception as e:
                print(f"❌ Erro ao criar issue: {e}")

if __name__ == "__main__":
    creator = GitHubIssueCreator()
    creator.run()
