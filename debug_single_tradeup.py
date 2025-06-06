"""
Debug script to directly test single collection trade-up calculation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import asyncio
from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def debug_single_tradeup():
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(sample_size=100)
    
    # Use the database manager directly to get test data
    from src.comprehensive_database import ComprehensiveDatabaseManager
    db_manager = ComprehensiveDatabaseManager()
    
    # Get skins from a specific collection and rarity for testing
    target_collection = 'The 2018 Inferno Collection'
    input_rarity = 'Consumer Grade'
    
    # Get Consumer Grade skins from this collection
    input_skins = db_manager.get_skins_by_collection_and_rarity(target_collection, input_rarity)
    
    if len(input_skins) < 10:
        print(f"❌ Only found {len(input_skins)} skins from collection {target_collection}, rarity {input_rarity}")
        # Try a different collection
        collections = db_manager.get_collections_by_rarity(input_rarity)
        print(f"Available collections with {input_rarity}: {collections[:5]}")
        if collections:
            target_collection = collections[0]
            input_skins = db_manager.get_skins_by_collection_and_rarity(target_collection, input_rarity)
    
    if len(input_skins) < 10:
        print(f"❌ Still only found {len(input_skins)} skins from collection {target_collection}")
        return
    print(f"🎯 Testing with {len(input_skins)} skins from collection: {target_collection}")
    print(f"Input rarity: {input_rarity}")
    print(f"Input skins: {[skin['market_hash_name'] for skin in input_skins[:3]]}...")
    
    try:
        # Call the single collection method directly
        print(f"📞 Calling _calculate_single_collection_tradeup with:")
        print(f"  Collection: {target_collection}")
        print(f"  Input rarity: {input_rarity}")
        print(f"  Input skins count: {len(input_skins)}")
        print(f"  Max input price: None")
        print(f"  Min profit: -100.0")
        
        result = await finder._calculate_single_collection_tradeup(
            target_collection,
            input_rarity,
            input_skins,
            None,  # max_input_price
            -100.0  # min_profit
        )
        
        print(f"🔍 Method returned: {result is not None}")
        
        if result:
            print("\n🔍 Debugging Output Attributes:")
            print(f"Number of output skins: {len(result.output_skins)}")
            
            for i, output in enumerate(result.output_skins[:3]):  # Check first 3
                print(f"\nOutput {i+1}: {output.skin.name}")
                print(f"  Has predicted_condition: {hasattr(output, 'predicted_condition')}")
                print(f"  Has predicted_float: {hasattr(output, 'predicted_float')}")
                
                if hasattr(output, 'predicted_condition'):
                    print(f"  predicted_condition: {output.predicted_condition}")
                if hasattr(output, 'predicted_float'):
                    print(f"  predicted_float: {output.predicted_float}")
                
                print(f"  skin.float_mid: {getattr(output.skin, 'float_mid', 'NOT_FOUND')}")
                print(f"  probability: {output.probability}")
                
            # Check if probabilities are equal (they should be for single collection)
            probabilities = [output.probability for output in result.output_skins]
            unique_probs = set(probabilities)
            print(f"\n📊 Probability Analysis:")
            print(f"  Total outputs: {len(probabilities)}")
            print(f"  Unique probabilities: {len(unique_probs)}")
            print(f"  Expected probability: {100/len(probabilities):.1f}%")
            if len(unique_probs) == 1:
                print(f"  ✅ All probabilities equal: {probabilities[0]:.1f}%")
            else:
                print(f"  ❌ Unequal probabilities: {unique_probs}")
                
        else:
            print("❌ No result returned from single collection calculation")
            
            # Let's debug why it returned None
            print("\n🔍 Debugging potential issues:")
            
            # Check if we have output skins for this collection
            output_rarity = 'Industrial Grade'  # Consumer -> Industrial
            output_skins = db_manager.get_skins_by_collection_and_rarity(target_collection, output_rarity)
            print(f"  Output skins in {target_collection} {output_rarity}: {len(output_skins)}")
            
            if output_skins:
                print(f"  Sample outputs: {[skin['market_hash_name'] for skin in output_skins[:3]]}")
            
            # Check pricing cache
            print(f"  Cached prices count: {len(finder._cached_prices)}")
            
            # Check if any input skin has pricing
            input_has_pricing = any(skin['market_hash_name'] in finder._cached_prices for skin in input_skins[:5])
            print(f"  Input skins have pricing: {input_has_pricing}")
            
            # Check if any output skin has pricing
            output_has_pricing = any(skin['market_hash_name'] in finder._cached_prices for skin in output_skins[:5])
            print(f"  Output skins have pricing: {output_has_pricing}")
            
    except Exception as e:
        print(f"❌ Error in calculation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_single_tradeup())
