"""
Test getting more comprehensive pricing data
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.runtime_pricing import RuntimePricingClient

async def test_comprehensive_pricing():
    print("Testing comprehensive pricing data...")
    
    try:
        client = RuntimePricingClient()
        
        # Try to get much larger sample
        print("Getting large sample of prices...")
        large_sample = await client.get_sample_prices(limit=5000)
        print(f"Got {len(large_sample)} prices")
        
        # Check specific skins we know should exist
        test_skins = [
            "Glock-18 | High Beam (Factory New)",
            "MAC-10 | Calf Skin (Battle-Scarred)", 
            "PP-Bizon | Candy Apple (Factory New)",
            "R8 Revolver | Nitro (Factory New)",
            "AK-47 | Redline (Field-Tested)",
            "M4A4 | Howl (Factory New)"
        ]
        
        print(f"\nChecking specific skins:")
        found_count = 0
        for skin in test_skins:
            if skin in large_sample:
                print(f"  ✅ {skin}: ${large_sample[skin]}")
                found_count += 1
            else:
                print(f"  ❌ {skin}: Not found")
        
        print(f"\nFound {found_count}/{len(test_skins)} test skins")
        
        # Try to load ALL prices if possible
        print(f"\nTrying to load ALL available prices...")
        await client._load_all_prices()
        all_prices = client._price_cache
        print(f"Full cache has {len(all_prices)} prices")
        
        # Check test skins again
        print(f"\nChecking test skins in full cache:")
        found_count = 0
        for skin in test_skins:
            if skin in all_prices:
                print(f"  ✅ {skin}: ${all_prices[skin]}")
                found_count += 1
            else:
                print(f"  ❌ {skin}: Not found")
        
        print(f"\nFound {found_count}/{len(test_skins)} test skins in full cache")
        
        # Look for patterns in what we do have
        print(f"\nAnalyzing what types of items we have prices for:")
        
        weapon_counts = {}
        condition_counts = {}
        
        for item_name in list(all_prices.keys())[:100]:  # Sample first 100
            if '|' in item_name and '(' in item_name:
                weapon = item_name.split('|')[0].strip()
                if '(' in item_name and item_name.endswith(')'):
                    condition = item_name.split('(')[-1].replace(')', '')
                    condition_counts[condition] = condition_counts.get(condition, 0) + 1
                
                weapon_counts[weapon] = weapon_counts.get(weapon, 0) + 1
        
        print(f"Top weapons by count:")
        for weapon, count in sorted(weapon_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {weapon}: {count}")
        
        print(f"Conditions found:")
        for condition, count in sorted(condition_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {condition}: {count}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_comprehensive_pricing())
