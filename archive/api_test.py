#!/usr/bin/env python3
"""
Quick test of PriceEmpire API connectivity
"""

import json
import requests

def test_api():
    # Load API key
    with open("config/secrets.json", "r") as f:
        secrets = json.load(f)
        api_key = secrets["api"]["priceempire_key"]
    
    print(f"API Key: {api_key[:10]}...")
    
    # Test API
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get("https://api.priceempire.com/v3/markets", headers=headers, timeout=10)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        markets = response.json()
        print(f"Found {len(markets)} markets")
        for i, market in enumerate(markets[:3]):
            print(f"  {market.get('name', 'Unknown')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_api()
