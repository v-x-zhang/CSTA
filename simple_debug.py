"""
Simple debug to check what's happening
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def simple_debug():
    print("Starting simple debug...")
    
    try:
        finder = ComprehensiveTradeUpFinder()
        print("Created finder")
        
        await finder.initialize(sample_size=100)
        print(f"Initialized with {len(finder._cached_prices)} prices")
        
        # Get collections
        collections = finder.db_manager.get_collections_by_rarity('Consumer Grade')
        print(f"Found {len(collections)} collections with Consumer Grade")
        
        if collections:
            test_collection = collections[0]
            print(f"Testing collection: {test_collection}")
            
            # Get skins
            consumer_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
            print(f"Found {len(consumer_skins)} consumer skins")
            
            if consumer_skins:
                print("Attempting single collection trade-up...")
                result = await finder._calculate_single_collection_tradeup(
                    test_collection,
                    'Consumer Grade', 
                    consumer_skins,
                    10.0,  # max_input_price
                    -5.0   # min_profit
                )
                
                if result:
                    print(f"SUCCESS! Profit: ${result.expected_profit:.2f}")
                else:
                    print("No result returned")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_debug())
