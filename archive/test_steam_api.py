#!/usr/bin/env python3
"""
Simple Steam Market API test
"""

import requests
import json

def test_steam_api():
    print("🧪 Testing Steam Market API")
    print("=" * 30)
    
    # Test with a common CS2 item
    item_name = "AK-47 | Blue Laminate (Field-Tested)"
    
    url = "https://steamcommunity.com/market/priceoverview/"
    params = {
        'country': 'US',
        'currency': '1',  # USD
        'appid': '730',   # CS2
        'market_hash_name': item_name
    }
    
    print(f"Testing item: {item_name}")
    print(f"URL: {url}")
    print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get('success'):
                if 'lowest_price' in data:
                    print(f"✅ Success! Price: {data['lowest_price']}")
                    print(f"Volume: {data.get('volume', 'N/A')}")
                else:
                    print("⚠️  No price data available")
            else:
                print("❌ API returned success=False")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_steam_api()
