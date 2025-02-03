# token_analyzer.py
import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
COINGECKO_PUBLIC_API = "https://api.coingecko.com/api/v3"
BINANCE_PUBLIC_API = "https://api.binance.com/api/v3"
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL')

def get_basic_token_info(identifier):
    """Get basic token info using public endpoints"""
    try:
        # Try CoinGecko list
        coins_list = requests.get(f"{COINGECKO_PUBLIC_API}/coins/list").json()
        
        # Search by symbol or name
        for coin in coins_list:
            if identifier.lower() in [coin['symbol'].lower(), coin['id'].lower()]:
                return coin
                
        # Search by contract address
        if identifier.startswith('0x'):
            eth_coin = requests.get(f"{COINGECKO_PUBLIC_API}/coins/ethereum").json()
            contracts = eth_coin.get('platforms', {})
            if identifier.lower() in contracts.values():
                return eth_coin
                
        return None
    except Exception as e:
        print(f"Error getting basic info: {str(e)}")
        return None

def get_historical_data(symbol):
    """Get historical data from Binance"""
    try:
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=90)).timestamp() * 1000)
        
        response = requests.get(
            f"{BINANCE_PUBLIC_API}/klines",
            params={
                'symbol': f"{symbol}USDT",
                'interval': '1d',
                'startTime': start_time,
                'endTime': end_time,
                'limit': 90
            }
        )
        
        if response.status_code == 200:
            return [{
                'time': entry[0],
                'price': float(entry[4])
            } for entry in response.json()]
            
        return None
    except Exception as e:
        print(f"Binance error: {str(e)}")
        return None

def analyze_with_ai(token_info, historical_data):
    """Analyze token with AI"""
    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL
    )
    
    system_prompt = """Przeanalizuj dane kryptowaluty:
    1. Analiza historycznych wzorców cenowych
    2. Identyfikacja kluczowych poziomów wsparcia/oporu
    3. Ocena aktualnych wskaźników technicznych
    4. Predykcja z prawdopodobieństwem (w %)
    5. Ryzyka i zalecenia
    
    Format:
    - [Sekcja] Szczegółowy opis w punktach"""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{token_info}\n{historical_data}"}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"AI error: {str(e)}")
        return None

def main():
    if not OPENAI_API_KEY:
        print("Brak klucza OpenAI w .env!")
        return
    
    identifier = input("Podaj ticker, nazwę lub adres kontraktu: ").strip()
    
    # Get basic info
    print("\nWyszukuję token...")
    token_info = get_basic_token_info(identifier)
    
    if not token_info:
        print("Nie znaleziono tokena!")
        return
    
    # Get historical data
    print("Pobieram dane historyczne...")
    symbol = token_info['symbol'].upper()
    historical_data = get_historical_data(symbol)
    
    if not historical_data:
        print("Brak danych historycznych!")
        return
    
    # AI Analysis
    print("Analizuję...")
    analysis = analyze_with_ai(token_info, historical_data)
    
    if analysis:
        filename = f"analiza_{symbol}_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(analysis)
        print(f"\nRaport zapisano w: {filename}")
    else:
        print("Analiza nie powiodła się")

if __name__ == "__main__":
    main()