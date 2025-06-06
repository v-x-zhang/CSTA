"""
Look for actual weapon skin matches between database and API
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_database import ComprehensiveDatabaseManager
from src.runtime_pricing import RuntimePricingClient

async def find_matches():
    print("Looking for actual matches...")
    
    try:
        # Get all database skin names
        db = ComprehensiveDatabaseManager()
        all_db_skins = []
        
        for rarity in ['Consumer Grade', 'Industrial Grade', 'Mil-Spec Grade']:
            collections = db.get_collections_by_rarity(rarity)
            for collection in collections[:3]:  # First few collections
                skins = db.get_skins_by_collection_and_rarity(collection, rarity)
                all_db_skins.extend([skin['market_hash_name'] for skin in skins])
        
        print(f"Got {len(all_db_skins)} database skins")
        
        # Get larger API sample
        client = RuntimePricingClient()
        api_prices = await client.get_sample_prices(limit=1000)
        api_names = set(api_prices.keys())
        
        print(f"Got {len(api_names)} API pricing entries")
        
        # Find direct matches
        db_names = set(all_db_skins)
        matches = db_names.intersection(api_names)
        
        print(f"\n=== DIRECT MATCHES: {len(matches)} ===")
        for match in list(matches)[:10]:
            price = api_prices[match]
            print(f"  {match}: ${price}")
        
        if len(matches) == 0:
            print("\n=== NO DIRECT MATCHES - CHECKING PATTERNS ===")
            
            # Look at weapon names in both sets
            db_weapons = set()
            api_weapons = set()
            
            for name in db_names:
                if '|' in name:
                    weapon = name.split('|')[0].strip()
                    db_weapons.add(weapon)
            
            for name in api_names:
                if '|' in name:
                    weapon = name.split('|')[0].strip()
                    api_weapons.add(weapon)
            
            common_weapons = db_weapons.intersection(api_weapons)
            print(f"Common weapons: {len(common_weapons)}")
            print(f"  Examples: {list(common_weapons)[:10]}")
            
            # Look for similar skin names
            print(f"\n=== SAMPLE COMPARISONS ===")
            for db_name in list(db_names)[:5]:
                if '|' in db_name:
                    weapon_skin = db_name.split('(')[0].strip()  # Remove condition
                    similar = [api_name for api_name in api_names if weapon_skin in api_name]
                    if similar:
                        print(f"DB: {db_name}")
                        print(f"    Similar: {similar[:3]}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(find_matches())
