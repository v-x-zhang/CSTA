"""
Check database skin names vs API pricing names
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_database import ComprehensiveDatabaseManager
from src.runtime_pricing import RuntimePricingClient

async def check_name_formats():
    print("Checking name format differences...")
    
    try:
        # Check database names
        db = ComprehensiveDatabaseManager()
        
        collections = db.get_collections_by_rarity('Consumer Grade')
        if collections:
            test_collection = collections[0]
            print(f"Testing collection: {test_collection}")
            
            consumer_skins = db.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
            
            print(f"\n=== Database skin names (first 5) ===")
            for skin in consumer_skins[:5]:
                print(f"  {skin['market_hash_name']}")
            
        # Check API names
        print(f"\n=== API pricing names (first 10) ===")
        client = RuntimePricingClient()
        sample_prices = await client.get_sample_prices(limit=20)
        
        for name in list(sample_prices.keys())[:10]:
            print(f"  {name}")
            
        # Look for patterns
        print(f"\n=== Looking for pattern differences ===")
        
        # Check if any database names appear in API
        db_names = {skin['market_hash_name'] for skin in consumer_skins}
        api_names = set(sample_prices.keys())
        
        matches = db_names.intersection(api_names)
        print(f"Direct matches: {len(matches)}")
        if matches:
            for match in list(matches)[:3]:
                print(f"  Match: {match}")
        
        # Check for partial matches (missing conditions)
        print(f"\n=== Checking for condition-related issues ===")
        for db_name in list(db_names)[:5]:
            # Extract base name (remove condition)
            if ' (' in db_name and db_name.endswith(')'):
                base_name = db_name.split(' (')[0]
                partial_matches = [api_name for api_name in api_names if base_name in api_name]
                if partial_matches:
                    print(f"DB: {db_name}")
                    print(f"    API matches: {partial_matches[:3]}")
            
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(check_name_formats())
