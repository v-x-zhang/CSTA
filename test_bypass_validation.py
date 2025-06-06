"""
Debug by bypassing price validation
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def test_bypass_validation():
    print("Testing trade-up with bypassed price validation...")
    
    try:
        finder = ComprehensiveTradeUpFinder()
        await finder.initialize(sample_size=2000)
        print(f"Initialized with {len(finder._cached_prices)} prices")
        
        # Test collection with known working data
        test_collection = "The 2018 Inferno Collection"
        consumer_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
        
        print(f"Testing collection: {test_collection}")
        print(f"Consumer skins: {len(consumer_skins)}")
        
        # First let's check if price validation is the issue
        print("\n=== Checking price validation status ===")
        
        for skin in consumer_skins[:5]:
            name = skin['market_hash_name']
            price = finder._cached_prices.get(name)
            if price:
                validation_status = finder.db_manager.get_price_validation_status(name)
                print(f"{name}: price=${price}, validation={validation_status}")
        
        # Now try a modified calculation that bypasses validation
        print("\n=== Manual calculation bypassing validation ===")
        
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
            print(f"Cheapest input: {cheapest_skin['market_hash_name']} @ ${cheapest_price}")
            
            # Get outputs
            output_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Industrial Grade')
            marketable_outputs = [skin for skin in output_skins if finder._is_marketable_skin(skin)]
              # Calculate expected output value WITHOUT validation checks
            total_cost = cheapest_price * 10
            expected_value = 0
            valid_outputs = 0
            
            print(f"All output skins:")
            for output_skin in marketable_outputs:
                price = finder._cached_prices.get(output_skin['market_hash_name'])
                print(f"  {output_skin['market_hash_name']}: ${price}")
                if price and float(price) > 0:
                    expected_value += float(price)
                    valid_outputs += 1
            
            if valid_outputs > 0:
                avg_output = expected_value / valid_outputs
                net_value = avg_output * 0.85  # Steam fee
                profit = net_value - total_cost
                
                print(f"\nCalculation (bypassing validation):")
                print(f"  Total input cost: ${total_cost}")
                print(f"  Average output value: ${avg_output}")
                print(f"  Net output value (after fees): ${net_value}")
                print(f"  Expected profit: ${profit}")
                print(f"  Meets -$5 min profit: {profit > -5}")
                
                if profit > -5:
                    print("\n✅ This SHOULD be found but validation is blocking it!")
                else:
                    print("\n❌ This trade wouldn't be profitable anyway")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(test_bypass_validation())
