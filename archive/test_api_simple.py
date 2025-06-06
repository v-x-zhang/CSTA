#!/usr/bin/env python3
"""
Simple test of PriceEmpire API connection
"""

import json
import requests

def test_connection():
    print("🧪 Testing PriceEmpire API Connection")
    print("=" * 40)
    
    # Load API key
    try:
        with open("config/secrets.json", "r") as f:
            secrets = json.load(f)
            api_key = secrets["api"]["priceempire_key"]
        print(f"✅ API key loaded: {api_key[:12]}...")
    except Exception as e:
        print(f"❌ Error loading API key: {e}")
        return False
    
    # Test API connection
    try:
        print("🔗 Testing connection to PriceEmpire API...")
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Test with basic request
        url = "https://api.pricempire.com/v4/paid/items/prices"
        params = {
            'app_id': 730,  # CS2
            'currency': 'USD'
        }
        
        print(f"Making request to: {url}")
        print(f"Headers: Authorization: Bearer {api_key[:10]}...")
        print(f"Params: {params}")
        
        response = requests.get(url, headers=headers, params=params, timeout=15)
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Received {len(data)} items")
            
            # Show first item as example
            if data:
                first_item = data[0]
                print(f"First item: {first_item.get('market_hash_name', 'Unknown')}")
                prices = first_item.get('prices', [])
                print(f"Available in {len(prices)} markets")
            
            return True
            
        elif response.status_code == 401:
            print("❌ Authentication failed - API key may be invalid")
            print(f"Response: {response.text}")
            return False
            
        else:
            print(f"❌ API Error: HTTP {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    if success:
        print("\n🎉 API connection successful!")
    else:
        print("\n💥 API connection failed!")
