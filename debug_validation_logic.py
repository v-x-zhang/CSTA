"""
Debug script to trace validation logic issues in single collection trade-up calculation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import asyncio
import logging
from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def debug_validation_logic():
    print("🔍 Debugging validation logic in single collection trade-up")
    
    # Initialize finder with Steam pricing
    finder = ComprehensiveTradeUpFinder(use_steam_pricing=True)
    await finder.initialize(use_all_prices=True)
    
    # Use the viable collection we found before
    target_collection = "The 2021 Dust 2 Collection"
    input_rarity = "Consumer Grade"
    
    print(f"🎯 Testing collection: {target_collection}")
    print(f"📊 Cached prices available: {len(finder._cached_prices)}")
    
    # Get input and output skins for this collection
    input_skins = finder.db_manager.get_skins_by_collection_and_rarity(target_collection, input_rarity)
    marketable_inputs = [skin for skin in input_skins if finder._is_marketable_skin(skin)]
    
    output_rarity = "Industrial Grade"
    all_output_skins = finder.db_manager.get_skins_by_collection_and_rarity(target_collection, output_rarity)
    marketable_outputs = [skin for skin in all_output_skins if finder._is_marketable_skin(skin)]
    
    print(f"📥 Marketable inputs: {len(marketable_inputs)}")
    print(f"📤 Marketable outputs: {len(marketable_outputs)}")
    
    # Test validation logic for inputs
    print("\n🔍 VALIDATION LOGIC FOR INPUTS:")
    input_with_pricing = []
    for skin in marketable_inputs[:5]:  # Check first 5
        name = skin['market_hash_name']
        price = finder._cached_prices.get(name)
        validation_status = finder.db_manager.get_price_validation_status(name)
        
        print(f"\nInput: {name}")
        print(f"  Price in cache: {price}")
        print(f"  Validation status: {validation_status}")
        
        if price:
            if validation_status and validation_status.get('status') == 'invalid':
                print(f"  ❌ SKIPPED - marked as invalid")
                continue
            elif validation_status and validation_status.get('status') == 'valid':
                steam_price = validation_status.get('steam_price')
                final_price = float(steam_price) if steam_price and steam_price > 0 else float(price)
                print(f"  ✅ VALID - using price: ${final_price}")
                input_with_pricing.append((skin, final_price))
            elif validation_status is None or validation_status.get('status') == 'unvalidated':
                print(f"  ⚠️ UNVALIDATED - using price: ${float(price)}")
                input_with_pricing.append((skin, float(price)))
    
    print(f"\n📥 Inputs with valid pricing: {len(input_with_pricing)}")
    
    # Test validation logic for outputs
    print("\n🔍 VALIDATION LOGIC FOR OUTPUTS:")
    output_with_pricing = []
    for skin in marketable_outputs[:5]:  # Check first 5
        name = skin['market_hash_name']
        base_name = finder._extract_base_skin_name(name)
        price = finder._cached_prices.get(name)
        validation_status = finder.db_manager.get_price_validation_status(base_name)
        
        print(f"\nOutput: {name}")
        print(f"  Base name: {base_name}")
        print(f"  Price in cache: {price}")
        print(f"  Validation status: {validation_status}")
        
        if price and float(price) > 0:
            if validation_status and validation_status.get('status') == 'valid':
                steam_price = validation_status.get('steam_price')
                final_price = float(steam_price) if steam_price and steam_price > 0 else float(price)
                print(f"  ✅ VALID - using price: ${final_price}")
                output_with_pricing.append((skin, final_price))
            elif validation_status is None or validation_status.get('status') == 'unvalidated':
                print(f"  ⚠️ UNVALIDATED - using price: ${float(price)}")
                output_with_pricing.append((skin, float(price)))
            else:
                print(f"  ❌ INVALID or no validation - status: {validation_status}")
    
    print(f"\n📤 Outputs with valid pricing: {len(output_with_pricing)}")
    
    # Try to manually check what happens in the method
    if input_with_pricing and output_with_pricing:
        print("\n🎯 MANUAL CALCULATION:")
        cheapest_input, cheapest_price = min(input_with_pricing, key=lambda x: x[1])
        total_input_cost = cheapest_price * 10
        
        print(f"Cheapest input: {cheapest_input['market_hash_name']} @ ${cheapest_price}")
        print(f"Total input cost (10x): ${total_input_cost}")
        
        expected_output_value = 0
        for output_skin, output_price in output_with_pricing:
            probability = 1.0 / len(output_with_pricing)
            expected_output_value += output_price * probability
            print(f"  {output_skin['market_hash_name']}: ${output_price} (prob: {probability:.3f})")
        
        expected_output_value *= 0.85  # Steam fee
        expected_profit = expected_output_value - total_input_cost
        
        print(f"\nExpected output value: ${expected_output_value:.2f}")
        print(f"Expected profit: ${expected_profit:.2f}")
        print(f"ROI: {(expected_profit / total_input_cost * 100):.1f}%")
        
        if expected_profit > -100:  # Our min_profit threshold
            print("✅ This should pass the profit check!")
        else:
            print("❌ This would fail the profit check")
    
    # Now test the actual method
    print("\n🔬 TESTING ACTUAL METHOD:")
    try:
        result = await finder._calculate_single_collection_tradeup(
            target_collection,
            input_rarity,
            input_skins,
            None,  # max_input_price
            -100.0  # min_profit
        )
        
        print(f"Method result: {result is not None}")
        if result:
            print(f"✅ SUCCESS! Found trade-up with profit: ${result.raw_profit}")
        else:
            print("❌ Method returned None - something is filtering out the results")
    except Exception as e:
        print(f"❌ Method failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_validation_logic())
