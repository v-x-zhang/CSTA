#!/usr/bin/env python3
"""
Test free PriceEmpire API endpoints
"""

import json
import requests

def test_free_endpoints():
    print("🆓 Testing PriceEmpire Free API Endpoints")
    print("=" * 45)
    
    # Load API key
    try:
        with open("config/secrets.json", "r") as f:
            secrets = json.load(f)
            api_key = secrets["api"]["priceempire_key"]
        print(f"✅ API key loaded: {api_key[:12]}...")
    except Exception as e:
        print(f"❌ Error loading API key: {e}")
        return False
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test different endpoints to see which are free
    test_endpoints = [
        # Try some endpoints that might be free
        ("Items Images", "https://api.pricempire.com/v4/paid/items/images", {'app_id': 730}),
        ("All Items", "https://api.pricempire.com/v4/paid/items", {'language': 'en'}),
        ("Item Metadata", "https://api.pricempire.com/v4/paid/items/metas", {}),
        
        # Try v3 endpoints in case they're still available
        ("V3 Items", "https://api.pricempire.com/v3/items", {}),
        ("V3 Markets", "https://api.pricempire.com/v3/markets", {}),
        
        # Try without auth to see if there are public endpoints
        ("Public Items", "https://api.pricempire.com/v4/items", {}),
        ("Public Prices", "https://api.pricempire.com/v4/prices", {}),
    ]
    
    working_endpoints = []
    
    for name, url, params in test_endpoints:
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            # Try with auth first
            response = requests.get(url, headers=headers, params=params, timeout=10)
            print(f"   With auth: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success! Data type: {type(data)}")
                if isinstance(data, list):
                    print(f"   📊 Received {len(data)} items")
                elif isinstance(data, dict):
                    print(f"   📋 Keys: {list(data.keys())[:5]}")
                working_endpoints.append((name, url, params, True))
                
            elif response.status_code == 401:
                print(f"   ❌ Auth required")
                
                # Try without auth
                response_no_auth = requests.get(url, params=params, timeout=10)
                print(f"   Without auth: {response_no_auth.status_code}")
                
                if response_no_auth.status_code == 200:
                    print(f"   ✅ Works without auth!")
                    working_endpoints.append((name, url, params, False))
                    
            else:
                print(f"   ❌ Error: {response.status_code}")
                if response.text:
                    print(f"   Message: {response.text[:100]}")
                    
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n{'='*45}")
    print(f"📊 SUMMARY:")
    print(f"Found {len(working_endpoints)} working endpoints:")
    
    for name, url, params, needs_auth in working_endpoints:
        auth_str = "🔐" if needs_auth else "🌐"
        print(f"   {auth_str} {name}: {url}")
    
    return len(working_endpoints) > 0

if __name__ == "__main__":
    success = test_free_endpoints()
    if success:
        print("\n🎉 Found working endpoints!")
    else:
        print("\n💥 No working endpoints found!")