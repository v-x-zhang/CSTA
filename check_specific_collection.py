"""
Check specific collection for matches
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_database import ComprehensiveDatabaseManager
from src.runtime_pricing import RuntimePricingClient

async def check_specific_collection():
    print("Checking specific collection...")
    
    try:
        db = ComprehensiveDatabaseManager()
        client = RuntimePricingClient()
        
        # Get large API sample
        api_prices = await client.get_sample_prices(limit=2000)
        print(f"Got {len(api_prices)} API prices")
        
        # Check the specific collection we were testing
        test_collection = "The 2018 Inferno Collection"
        consumer_skins = db.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
        output_skins = db.get_skins_by_collection_and_rarity(test_collection, 'Industrial Grade')
        
        print(f"\n=== {test_collection} ===")
        print(f"Consumer skins: {len(consumer_skins)}")
        print(f"Output skins: {len(output_skins)}")
        
        # Check for matches
        consumer_matches = []
        output_matches = []
        
        for skin in consumer_skins:
            name = skin['market_hash_name']
            if name in api_prices:
                consumer_matches.append((name, api_prices[name]))
        
        for skin in output_skins:
            name = skin['market_hash_name']
            if name in api_prices:
                output_matches.append((name, api_prices[name]))
        
        print(f"\nConsumer matches: {len(consumer_matches)}")
        for name, price in consumer_matches[:5]:
            print(f"  {name}: ${price}")
        
        print(f"\nOutput matches: {len(output_matches)}")
        for name, price in output_matches[:5]:
            print(f"  {name}: ${price}")
        
        # Calculate if this could work        if consumer_matches and output_matches:
            cheapest_input = min(consumer_matches, key=lambda x: float(x[1]))
            total_cost = float(cheapest_input[1]) * 10
            avg_output = sum(float(price) for _, price in output_matches) / len(output_matches)
            expected_value = avg_output * 0.85  # Steam fee
            profit = expected_value - total_cost
            
            print(f"\n=== Manual Calculation ===")
            print(f"Cheapest input: {cheapest_input[0]} @ ${cheapest_input[1]}")
            print(f"Total input cost: ${total_cost}")
            print(f"Average output value: ${avg_output}")
            print(f"Expected output value (after fees): ${expected_value}")
            print(f"Expected profit: ${profit}")
            print(f"Would meet -$5 min profit: {profit > -5}")
        else:
            print("\nInsufficient matches for trade-up calculation")
        
        # Try a different collection with more matches
        print(f"\n=== Trying different collections ===")
        for rarity in ['Consumer Grade']:
            collections = db.get_collections_by_rarity(rarity)
            for collection in collections[:5]:
                skins = db.get_skins_by_collection_and_rarity(collection, rarity)
                matches = sum(1 for skin in skins if skin['market_hash_name'] in api_prices)
                if matches > 5:
                    print(f"{collection}: {matches}/{len(skins)} matches")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(check_specific_collection())
