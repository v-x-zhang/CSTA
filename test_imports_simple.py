#!/usr/bin/env python3
"""
Simple test to check if imports work
"""

import sys
from pathlib import Path
import asyncio

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

async def test_imports():
    try:
        print("Testing imports...")
        
        # Test database manager
        from comprehensive_database import ComprehensiveDatabaseManager
        print("✅ ComprehensiveDatabaseManager imported")
        
        # Test runtime pricing
        from runtime_pricing import RuntimePricingClient
        print("✅ RuntimePricingClient imported")
        
        # Test CSFloat client
        from csfloat_listings import CSFloatListingsClient
        print("✅ CSFloatListingsClient imported")
        
        # Test comprehensive finder
        from comprehensive_trade_finder import ComprehensiveTradeUpFinder
        print("✅ ComprehensiveTradeUpFinder imported")
        
        # Try to initialize
        print("\nTesting initialization...")
        db_manager = ComprehensiveDatabaseManager()
        print("✅ Database manager initialized")
        
        # Test getting some basic info
        print("\nTesting database access...")
        tradeable_skins = db_manager.get_all_tradeable_skins()
        print(f"✅ Found {len(tradeable_skins)} tradeable skins")
        
        print("\n✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_imports())
