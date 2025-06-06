"""
Detailed debug to check what's happening in _calculate_single_collection_tradeup
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def debug_single_collection():
    print("Starting detailed debug of single collection trade-up...")
    
    try:
        print("About to create finder...")
        finder = ComprehensiveTradeUpFinder()
        print("Created finder successfully")
        
        await finder.initialize(sample_size=200)
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
            
            # Get output skins  
            output_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Industrial Grade')
            print(f"Found {len(output_skins)} output skins")
            
            if consumer_skins and output_skins:
                print("\n=== DEBUG: Checking pricing data ===")
                
                # Check prices for first few consumer skins
                print("Consumer skin prices:")
                for i, skin in enumerate(consumer_skins[:5]):
                    price = finder._cached_prices.get(skin['market_hash_name'])
                    print(f"  {skin['market_hash_name']}: {price}")
                
                print("\nOutput skin prices:")
                for i, skin in enumerate(output_skins[:5]):
                    price = finder._cached_prices.get(skin['market_hash_name'])
                    print(f"  {skin['market_hash_name']}: {price}")
                
                print("\n=== DEBUG: Manual calculation ===")
                
                # Find cheapest consumer skin
                cheapest_price = float('inf')
                cheapest_skin = None
                for skin in consumer_skins:
                    price = finder._cached_prices.get(skin['market_hash_name'])
                    if price and float(price) <= 10.0:  # max_input_price
                        if float(price) < cheapest_price:
                            cheapest_price = float(price)
                            cheapest_skin = skin
                
                if cheapest_skin:
                    print(f"Cheapest consumer skin: {cheapest_skin['market_hash_name']} @ ${cheapest_price}")
                    total_input_cost = cheapest_price * 10
                    print(f"Total input cost: ${total_input_cost}")
                    
                    # Calculate expected output value
                    expected_output_value = 0
                    valid_outputs = 0
                    for output_skin in output_skins:
                        price = finder._cached_prices.get(output_skin['market_hash_name'])
                        if price:
                            expected_output_value += float(price)
                            valid_outputs += 1
                    
                    if valid_outputs > 0:
                        expected_output_value = (expected_output_value / valid_outputs) * 0.85  # Steam fee
                        expected_profit = expected_output_value - total_input_cost
                        print(f"Expected output value: ${expected_output_value}")
                        print(f"Expected profit: ${expected_profit}")
                        print(f"Meets min_profit of -$5.00: {expected_profit > -5.0}")
                    else:
                        print("No valid output prices found!")
                else:
                    print("No valid consumer skin found within price limit!")
                
                print("\n=== Running actual method ===")
                result = await finder._calculate_single_collection_tradeup(
                    test_collection,
                    'Consumer Grade', 
                    consumer_skins,
                    10.0,  # max_input_price
                    -5.0   # min_profit
                )
                
                if result:
                    print(f"SUCCESS! Result: {result}")
                    print(f"  Expected profit: ${result.expected_profit:.2f}")
                    print(f"  ROI: {result.roi_percentage:.2f}%")
                else:
                    print("Method returned None")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_single_collection())
