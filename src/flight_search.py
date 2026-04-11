import os
from amadeus import Client, ResponseError
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class FlightSearch:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv("AMADEUS_CLIENT_ID"),
            client_secret=os.getenv("AMADEUS_CLIENT_SECRET")
        )
    
    def search_flights(self, origin: str, destination: str, 
                       departure_date: str, return_date: str = None):
        """
        Busca voos usando Amadeus API
        Retorna: voo mais barato encontrado
        """
        try:
            response = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=destination,
                departureDate=departure_date,
                returnDate=return_date,
                adults=1,
                max=5,
                currencyCode='BRL'
            )
            
            flights = []
            for offer in response.data:
                price = float(offer['price']['total'])
                airline = offer['validatingAirlineCodes'][0]
                
                flights.append({
                    'price': price,
                    'airline': airline,
                    'currency': offer['price']['currency'],
                    'departure': offer['itineraries'][0]['segments'][0]['departure']['at'],
                    'arrival': offer['itineraries'][0]['segments'][-1]['arrival']['at']
                })
            
            # Retorna o mais barato
            return min(flights, key=lambda x: x['price']) if flights else None
            
        except ResponseError as error:
            print(f"Erro na API Amadeus: {error}")
            return None
