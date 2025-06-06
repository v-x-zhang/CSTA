"""
Debug pricing data to understand the mismatch
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def debug_pricing():
    print("Starting pricing debug...")
    
    try:
        finder = ComprehensiveTradeUpFinder()
        print("Created finder")
        
        # Initialize with small sample
        await finder.initialize(sample_size=50)
        print(f"Initialized with {len(finder._cached_prices)} prices")
        
        # Show what's actually in the cache
        print("\n=== Cached prices sample ===")
        count = 0
        for name, price in finder._cached_prices.items():
            if count < 10:
                print(f"  {name}: ${price}")
                count += 1
            else:
                break
        
        # Get a collection and check naming patterns
        collections = finder.db_manager.get_collections_by_rarity('Consumer Grade')
        if collections:
            test_collection = collections[0]
            consumer_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
            
            print(f"\n=== Database skin names from {test_collection} ===")
            for i, skin in enumerate(consumer_skins[:10]):
                name = skin['market_hash_name']
                print(f"  DB: {name}")
                
                # Check if we have exact match
                price = finder._cached_prices.get(name)
                print(f"       Cache: {price}")
                
                # Check for similar names in cache
                similar = [cached_name for cached_name in finder._cached_prices.keys() 
                          if any(word in cached_name.lower() for word in name.lower().split()[:2])][:3]
                if similar:
                    print(f"       Similar: {similar}")
                print()
        
        # Check if pricing API is working at all
        print("\n=== Testing direct API call ===")
        try:
            test_names = ["AK-47 | Redline (Field-Tested)", "Glock-18 | Water Elemental (Minimal Wear)"]
            prices = await finder.pricing_client.fetch_prices_for_items(test_names)
            print(f"Direct API result for {test_names}: {prices}")
        except Exception as e:
            print(f"Direct API call failed: {e}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_pricing())
