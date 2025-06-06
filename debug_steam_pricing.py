"""
Debug script using Steam pricing database for single collection trade-up calculation
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.comprehensive_database import ComprehensiveDatabaseManager

async def debug_with_steam_pricing():
    print("🎯 Testing Single Collection Trade-up with Steam Pricing")
    print("=" * 60)
    
    try:
        # Initialize database manager
        db_manager = ComprehensiveDatabaseManager()
        
        # Initialize trade finder with Steam pricing
        print("🔄 Initializing finder with Steam pricing database...")
        finder = ComprehensiveTradeUpFinder(use_steam_pricing=True)
        await finder.initialize(use_all_prices=True)
        
        print(f"✅ Initialized with {len(finder._cached_prices)} Steam prices")
        
        # Show sample of what skins we DO have pricing for
        print(f"\n🔍 Sample of skins with Steam pricing:")
        cache_sample = list(finder._cached_prices.items())[:10]
        for name, price in cache_sample:
            print(f"  {name}: ${price}")
        
        # Test parameters
        input_rarity = "Consumer Grade"
        
        # Find a collection where both inputs and outputs have pricing
        print(f"\n🔍 Searching for collections with pricing data...")
        collections = db_manager.get_collections_by_rarity(input_rarity)
        
        viable_collection = None
        for collection_name in collections[:10]:  # Check first 10 collections
            input_skins = db_manager.get_skins_by_collection_and_rarity(collection_name, input_rarity)
            output_skins = db_manager.get_skins_by_collection_and_rarity(collection_name, 'Industrial Grade')
            
            if len(input_skins) >= 10 and len(output_skins) >= 1:
                # Check if we have pricing for inputs and outputs
                input_has_pricing = any(skin['market_hash_name'] in finder._cached_prices for skin in input_skins[:10])
                output_has_pricing = any(skin['market_hash_name'] in finder._cached_prices for skin in output_skins[:5])
                
                print(f"  {collection_name}: inputs={input_has_pricing}, outputs={output_has_pricing}")
                
                if input_has_pricing and output_has_pricing:
                    viable_collection = collection_name
                    break
        
        if not viable_collection:
            print("❌ No viable collections found with pricing data")
            return
            
        target_collection = viable_collection
        
        # Get input skins
        input_skins = db_manager.get_skins_by_collection_and_rarity(target_collection, input_rarity)
        
        print(f"🎯 Testing with {len(input_skins)} skins from collection: {target_collection}")
        print(f"Input rarity: {input_rarity}")
        print(f"Input skins: {[skin['market_hash_name'] for skin in input_skins[:3]]}...")
        
        # Check pricing data availability
        input_has_pricing = any(skin['market_hash_name'] in finder._cached_prices for skin in input_skins[:5])
        print(f"🔍 Input skins have pricing: {input_has_pricing}")
        
        if input_has_pricing:
            for skin in input_skins[:3]:
                name = skin['market_hash_name']
                price = finder._cached_prices.get(name, 'No price')
                print(f"  {name}: ${price}")
        
        # Get output skins
        output_rarity = 'Industrial Grade'  # Consumer -> Industrial
        output_skins = db_manager.get_skins_by_collection_and_rarity(target_collection, output_rarity)
        print(f"🎯 Output skins in {target_collection} {output_rarity}: {len(output_skins)}")
        
        output_has_pricing = any(skin['market_hash_name'] in finder._cached_prices for skin in output_skins[:5])
        print(f"🔍 Output skins have pricing: {output_has_pricing}")
        
        if output_has_pricing:
            for skin in output_skins[:3]:
                name = skin['market_hash_name']
                price = finder._cached_prices.get(name, 'No price')
                print(f"  {name}: ${price}")
        
        # Try the single collection calculation
        print(f"\n📞 Calling _calculate_single_collection_tradeup...")
        result = await finder._calculate_single_collection_tradeup(
            target_collection,
            input_rarity,
            input_skins,
            None,  # max_input_price
            -100.0  # min_profit
        )
        
        print(f"🔍 Method returned: {result is not None}")
        if result:
            print("\n🎉 SUCCESS! Trade-up calculation worked!")
            print(f"Number of output skins: {len(result.output_skins)}")
            print(f"Input cost: ${result.input_config.total_cost:.2f}")
            print(f"Expected value: ${result.expected_output_price:.2f}")
            print(f"Raw profit: ${result.raw_profit:.2f}")
            
            print("\n🔍 Checking output attributes:")
            for i, output in enumerate(result.output_skins[:3]):
                print(f"\nOutput {i+1}: {output.skin.name}")
                print(f"  Probability: {output.probability:.1f}%")
                print(f"  Has predicted_condition: {hasattr(output, 'predicted_condition')}")
                print(f"  Has predicted_float: {hasattr(output, 'predicted_float')}")
                
                if hasattr(output, 'predicted_condition'):
                    print(f"  predicted_condition: {output.predicted_condition}")
                if hasattr(output, 'predicted_float'):
                    print(f"  predicted_float: {output.predicted_float}")
                    
            # Check probabilities
            probabilities = [output.probability for output in result.output_skins]
            unique_probs = list(set(probabilities))
            
            print(f"\n📊 Probability Analysis:")
            print(f"  Total outputs: {len(probabilities)}")
            print(f"  Unique probabilities: {len(unique_probs)}")
            print(f"  Expected probability: {100/len(probabilities):.1f}%")
            if len(unique_probs) == 1:
                print(f"  ✅ All probabilities equal: {probabilities[0]:.1f}%")
            else:
                print(f"  ❌ Unequal probabilities: {unique_probs}")
        else:
            print("❌ Still no result returned from single collection calculation")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_with_steam_pricing())
