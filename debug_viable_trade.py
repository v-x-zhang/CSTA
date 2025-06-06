"""
Debug why the trade-up method fails with known viable trade
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def debug_known_viable_trade():
    print("Debugging known viable trade...")
    
    try:
        finder = ComprehensiveTradeUpFinder()
        await finder.initialize(sample_size=2000)
        print(f"Initialized with {len(finder._cached_prices)} prices")
        
        # Test the exact collection we know has a viable trade
        test_collection = "The 2018 Inferno Collection"
        consumer_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
        output_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Industrial Grade')
        
        print(f"Collection: {test_collection}")
        print(f"Consumer skins: {len(consumer_skins)}")
        print(f"Output skins: {len(output_skins)}")
        
        # Check what prices we have
        consumer_with_prices = []
        output_with_prices = []
        
        for skin in consumer_skins:
            price = finder._cached_prices.get(skin['market_hash_name'])
            if price:
                consumer_with_prices.append((skin, float(price)))
        
        for skin in output_skins:
            price = finder._cached_prices.get(skin['market_hash_name'])
            if price:
                output_with_prices.append((skin, float(price)))
        
        print(f"Consumer skins with prices: {len(consumer_with_prices)}")
        print(f"Output skins with prices: {len(output_with_prices)}")
        
        if consumer_with_prices and output_with_prices:
            # The method should find this, let's debug step by step
            print("\n=== Debugging method step by step ===")
            
            # Now call the actual method with debugging
            print("Calling _calculate_single_collection_tradeup...")
            result = await finder._calculate_single_collection_tradeup(
                test_collection,
                'Consumer Grade',
                consumer_skins,
                10.0,  # max_input_price
                -5.0   # min_profit
            )
            
            if result:
                print(f"SUCCESS! Found result:")
                print(f"  Expected profit: ${result.expected_profit:.2f}")
                print(f"  Input cost: ${result.input_config.total_cost}")
                print(f"  Output value: ${result.expected_output_price}")
            else:
                print("Method returned None - debugging why...")
                
                # Let's manually trace through the method logic
                print("\n=== Manual trace ===")
                
                # Step 1: Get output collection
                output_collection = finder.db_manager.get_output_collection('Consumer Grade')
                print(f"Output collection: {output_collection}")
                
                # Step 2: Get output skins
                output_skins_from_db = finder.db_manager.get_skins_by_collection_and_rarity(output_collection, 'Industrial Grade')
                print(f"Output skins from method: {len(output_skins_from_db)}")
                
                # This might be the issue - different output collection!
                if output_collection != test_collection:
                    print(f"WARNING: Output collection ({output_collection}) != input collection ({test_collection})")
                    
                    # Check if output collection has prices
                    output_skins_method = finder.db_manager.get_skins_by_collection_and_rarity(output_collection, 'Industrial Grade')
                    output_with_prices_method = []
                    for skin in output_skins_method:
                        price = finder._cached_prices.get(skin['market_hash_name'])
                        if price:
                            output_with_prices_method.append((skin, float(price)))
                    
                    print(f"Output skins with prices from method's collection: {len(output_with_prices_method)}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(debug_known_viable_trade())
