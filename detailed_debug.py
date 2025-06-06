#!/usr/bin/env python3
"""
Debug script with detailed logging to find exactly where the method fails
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def debug_with_logging():
    print("=== Detailed Debug Analysis ===\n")
    
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(sample_size=100)
    
    # Get a test collection
    collections = finder.db_manager.get_collections_by_rarity('Consumer Grade')
    test_collection = collections[0]
    print(f"Testing collection: {test_collection}")
    
    # Get skins
    consumer_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Consumer Grade')
    industrial_skins = finder.db_manager.get_skins_by_collection_and_rarity(test_collection, 'Industrial Grade')
    
    print(f"Consumer skins: {len(consumer_skins)}")
    print(f"Industrial skins: {len(industrial_skins)}")
    
    if not industrial_skins:
        print("❌ No industrial skins found - cannot create trade-up")
        return
    
    # Check marketable status
    def is_marketable(skin):
        return (skin.get('stattrak', False) == False and 
                skin.get('souvenir', False) == False and
                skin.get('weapon_name') and 
                skin.get('skin_name'))
    
    marketable_consumer = [s for s in consumer_skins if is_marketable(s)]
    marketable_industrial = [s for s in industrial_skins if is_marketable(s)]
    
    print(f"Marketable consumer skins: {len(marketable_consumer)}")
    print(f"Marketable industrial skins: {len(marketable_industrial)}")
    
    if not marketable_industrial:
        print("❌ No marketable industrial skins found")
        return
    
    # Check pricing
    consumer_with_prices = 0
    industrial_with_prices = 0
    
    for skin in marketable_consumer[:10]:
        if skin['market_hash_name'] in finder._cached_prices:
            consumer_with_prices += 1
            price = finder._cached_prices[skin['market_hash_name']]
            print(f"  Consumer: {skin['market_hash_name']} = ${price}")
            
    for skin in marketable_industrial[:10]:
        if skin['market_hash_name'] in finder._cached_prices:
            industrial_with_prices += 1
            price = finder._cached_prices[skin['market_hash_name']]
            print(f"  Industrial: {skin['market_hash_name']} = ${price}")
    
    print(f"\nPricing availability:")
    print(f"Consumer skins with prices: {consumer_with_prices}/{len(marketable_consumer)}")
    print(f"Industrial skins with prices: {industrial_with_prices}/{len(marketable_industrial)}")
    
    # Check validation status
    print(f"\nValidation status check:")
    for skin in marketable_consumer[:5]:
        validation = finder.db_manager.get_price_validation_status(skin['market_hash_name'])
        status = validation.get('status', 'unvalidated') if validation else 'unvalidated'
        print(f"  {skin['market_hash_name']}: {status}")
    
    # Try to find at least one valid input
    print(f"\nLooking for valid inputs...")
    valid_inputs = []
    for condition in ['Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred']:
        condition_inputs = [s for s in marketable_consumer if s.get('condition_name') == condition]
        print(f"  {condition}: {len(condition_inputs)} skins")
        
        for skin in condition_inputs[:3]:  # Check first 3
            price = finder._cached_prices.get(skin['market_hash_name'])
            if price and float(price) <= 10.0:  # max_input_price
                validation = finder.db_manager.get_price_validation_status(skin['market_hash_name'])
                if not validation or validation.get('status') != 'invalid':
                    valid_inputs.append((skin, price))
                    print(f"    ✅ Valid: {skin['market_hash_name']} = ${price}")
                else:
                    print(f"    ❌ Invalid: {skin['market_hash_name']} = ${price}")
            else:
                print(f"    ❌ No price or too expensive: {skin['market_hash_name']}")
    
    print(f"\nFound {len(valid_inputs)} valid inputs")
    
    if valid_inputs:
        # Check if we can get output prices
        print(f"\nChecking output pricing...")
        test_input = valid_inputs[0][0]
        input_float = finder._get_condition_float(test_input)
        print(f"Input float: {input_float}")
        
        valid_outputs = 0
        for output_skin in marketable_industrial[:5]:
            scaled_float, predicted_condition = finder._calculate_output_float_and_condition(input_float, output_skin)
            
            # Try to get price
            condition_name = f"{output_skin['market_hash_name']} ({predicted_condition})"
            base_name = output_skin['market_hash_name']
            
            price = finder._cached_prices.get(condition_name)
            if not price:
                price = finder._cached_prices.get(base_name)
            
            if price:
                validation = finder.db_manager.get_price_validation_status(base_name)
                status = validation.get('status', 'unvalidated') if validation else 'unvalidated'
                
                if status != 'invalid':
                    valid_outputs += 1
                    print(f"  ✅ {base_name}: ${price} (predicted: {predicted_condition}, status: {status})")
                else:
                    print(f"  ❌ {base_name}: ${price} (INVALID)")
            else:
                print(f"  ❌ {base_name}: No price")
        
        print(f"\nValid outputs: {valid_outputs}")
        
        if valid_outputs == 0:
            print("❌ No valid outputs found - this is likely why no trade-ups are found!")

if __name__ == "__main__":
    asyncio.run(debug_with_logging())
