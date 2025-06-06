#!/usr/bin/env python3
"""
Debug script for improved trade-up finder
"""

import json
import sys

def load_api_key():
    """Load API key from config"""
    try:
        print("Loading API key...")
        with open("config/secrets.json", "r") as f:
            secrets = json.load(f)
            key = secrets["api"]["priceempire_key"]
            print(f"✅ API key loaded: {key[:12]}...")
            return key
    except Exception as e:
        print(f"❌ Error loading API key: {e}")
        return None

def test_imports():
    """Test all imports"""
    print("Testing imports...")
    try:
        import requests
        print("✅ requests imported")
        
        import time
        print("✅ time imported")
        
        from typing import Dict, List, Tuple, Optional
        print("✅ typing imported")
        
        from dataclasses import dataclass
        print("✅ dataclasses imported")
        
        from collections import defaultdict
        print("✅ collections imported")
        
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    print("🔍 Debug Script for Improved Trade-Up Finder")
    print("=" * 50)
    
    # Test imports
    if not test_imports():
        print("❌ Import test failed")
        return
    
    # Test API key loading
    api_key = load_api_key()
    if not api_key:
        print("❌ API key test failed")
        return
    
    print("✅ All basic tests passed!")
    print("Now testing the main script...")
    
    # Try to import and run the main finder
    try:
        print("✅ ImprovedTradeUpFinder imported successfully")
        from improved_tradeup_finder import ImprovedTradeUpFinder
        finder=ImprovedTradeUpFinder(api_key)
        print("✅ ImprovedTradeUpFinder initialized")
        
        print("Testing API connection...")
        # Test a simple API call
        import requests
        response = requests.get(
            "https://api.pricempire.com/v4/paid/items/prices", 
            headers={"Authorization": f"Bearer {api_key}"},
            params={
                'app_id': 730,
                'language': 'en',
                'currency': 'USD'
            },
            timeout=10
        )
        print(f"API response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working! Got {len(data)} items")
        else:
            print(f"❌ API error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error in main script test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting debug script...")
    sys.stdout.flush()
    main()
    print("🏁 Debug script completed!")
    sys.stdout.flush()
