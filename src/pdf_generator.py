from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from datetime import datetime
import os

class AlertPDFGenerator:
    def __init__(self, supabase):
        self.supabase = supabase
        self.styles = getSampleStyleSheet()
        
    def create_alert_pdf(self, route_id, output_path="alert.pdf"):
        """Cria PDF formatado tipo grupo de milhas"""
        
        # Busca dados
        history = self.supabase.table("price_history").select("""
            *,
            monitored_routes (
                origin_city,
                destination_city,
                origin,
                destination,
                max_price
            )
        """).eq("route_id", route_id).order("created_at", desc=True).limit(1).execute()
        
        if not history.data:
            return None
            
        alert = history.data[0]
        route = alert['monitored_routes']
        
        # Cria PDF
        doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
        elements = []
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a237e'),
            alignment=1,  # Center
            spaceAfter=30
        )
        
        elements.append(Paragraph("🔥 ALERTA DE PASSAGENS!", title_style))
        elements.append(Spacer(1, 1*cm))
        
        # Rota principal
        route_text = f"<b>{route['origin_city']} ✈ {route['destination_city']}</b>"
        elements.append(Paragraph(route_text, self.styles['Heading2']))
        elements.append(Spacer(1, 0.5*cm))
        
        # Preço
        price_style = ParagraphStyle(
            'Price',
            fontSize=28,
            textColor=colors.HexColor('#2e7d32'),
            alignment=1,
            spaceAfter=20
        )
        elements.append(Paragraph(f"💰 R$ {alert['price']:.2f}", price_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Companhia
        elements.append(Paragraph(f"🛫 Companhia: {alert['airline']}", self.styles['Normal']))
        elements.append(Spacer(1, 0.3*cm))
        
        # Datas
        if alert.get('departure_date'):
            elements.append(Paragraph(
                f"📅 Ida: {alert['departure_date']}", 
                self.styles['Normal']
            ))
            elements.append(Spacer(1, 0.2*cm))
            
        if alert.get('return_date'):
            elements.append(Paragraph(
                f"📅 Volta: {alert['return_date']}", 
                self.styles['Normal']
            ))
            elements.append(Spacer(1, 0.5*cm))
        
        # Links
        if alert.get('google_flights_url'):
            elements.append(Paragraph(
                f"<b>🔗 Google Flights:</b> <link href='{alert['google_flights_url']}'>Clique aqui</link>",
                self.styles['Normal']
            ))
            elements.append(Spacer(1, 0.3*cm))
            
        if alert.get('skyscanner_url'):
            elements.append(Paragraph(
                f"<b>🔗 Skyscanner:</b> <link href='{alert['skyscanner_url']}'>Clique aqui</link>",
                self.styles['Normal']
            ))
        
        # Tabela de comparação
        elements.append(Spacer(1, 1*cm))
        
        data = [
            ['Preço Encontrado', f"R$ {alert['price']:.2f}"],
            ['Preço Máximo', f"R$ {route['max_price']:.2f}"],
            ['Economia', f"R$ {route['max_price'] - alert['price']:.2f}"]
        ]
        
        table = Table(data, colWidths=[5*cm, 3*cm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        
        # Rodapé
        elements.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle(
            'Footer',
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph(
            f"Alerta gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            footer_style
        ))
        
        # Build PDF
        doc.build(elements)
        return output_path
