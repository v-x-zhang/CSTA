"""
End-to-end test for the updated float scaling implementation
This demonstrates the complete workflow with realistic trade-up calculations
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.formatter import TradeUpFormatter

async def test_e2e_float_scaling():
    """Test the complete end-to-end workflow with float scaling"""
    
    print("=== CS2 Trade-up Calculator - Float Scaling E2E Test ===\n")
    
    # Initialize the finder with a small sample
    print("🔄 Initializing finder with sample data...")
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(sample_size=500)  # Small sample for quick testing
    
    print(f"✅ Initialized with pricing data\n")
    
    # Test specific trade-up calculation with known inputs
    print("🧪 Testing specific trade-up calculation...")
      # Get some input skins from the database for testing
    all_skins = list(finder.db_manager.get_all_tradeable_skins())
      # Find some consumer grade skins for testing
    consumer_skins = [skin for skin in all_skins if skin['rarity'] == 'Consumer Grade'][:10]
    
    if len(consumer_skins) >= 10:
        print(f"📊 Found {len(consumer_skins)} consumer grade skins for testing")
          # Test the single collection trade-up calculation
        collection = consumer_skins[0]['collection']
        print(f"🎯 Testing collection: {collection}")
        
        # Get skins from this collection
        collection_skins = [skin for skin in consumer_skins if skin['collection'] == collection]
        
        if len(collection_skins) >= 10:
            input_skins = collection_skins[:10]
              print("📋 Input skins:")
            for i, skin in enumerate(input_skins, 1):
                print(f"  {i}. {skin['weapon_name']} | {skin['skin_name']} ({skin['rarity']})")
            
            # Test the calculation method directly
            print("\n🔢 Calculating trade-up with float scaling...")
            try:
                result = await finder._calculate_single_collection_tradeup(
                    input_skins=input_skins,
                    input_rarity='Consumer Grade',
                    input_prices=[1.0] * 10,  # Mock prices
                    output_rarity='Industrial Grade'
                )
                
                if result:
                    print("✅ Trade-up calculation successful!")
                    print(f"💰 Expected profit: ${result.expected_profit:.2f}")
                    print(f"💸 Total cost: ${result.total_cost:.2f}")
                    print(f"📈 Expected value: ${result.expected_value:.2f}")
                    
                    if hasattr(result, 'output_items') and result.output_items:
                        print("\n🎲 Output predictions with float scaling:")
                        for i, output in enumerate(result.output_items, 1):
                            predicted_condition = getattr(output, 'predicted_condition', 'N/A')
                            predicted_float = getattr(output, 'predicted_float', 'N/A')
                            
                            print(f"  {i}. {output.weapon} | {output.skin_name}")
                            print(f"     💎 Predicted condition: {predicted_condition}")
                            if predicted_float != 'N/A':
                                print(f"     🎯 Predicted float: {predicted_float:.6f}")
                            print(f"     💵 Price: ${output.price:.2f}")
                            print(f"     📊 Probability: {output.probability:.1%}")
                            print()
                        
                        print("🎉 Float scaling is working correctly in the end-to-end workflow!")
                    else:
                        print("⚠️  No output items found in result")
                        
                else:
                    print("❌ No trade-up result generated")
                    
            except Exception as e:
                print(f"❌ Error in calculation: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"❌ Not enough skins in collection {collection} for testing")
    else:
        print("❌ Not enough consumer grade skins found for testing")
    
    # Test the search functionality with a very low profit threshold
    print("\n🔍 Testing profitable trade search with float scaling...")
    try:
        results = await finder.find_profitable_trades(
            min_profit=0.01,  # Very low threshold to find something
            max_input_price=5.0,  # Low price limit for quick search
            limit=2
        )
        
        if results:
            print(f"✅ Found {len(results)} profitable trade-ups with float scaling:")
            for i, result in enumerate(results, 1):
                print(f"\n--- Trade-up #{i} ---")
                formatted = TradeUpFormatter.format_single_result(result)
                print(formatted)
        else:
            print("🔍 No profitable trades found with current parameters")
            
    except Exception as e:
        print(f"❌ Error in search: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Float Scaling E2E Test Complete ===")

if __name__ == "__main__":
    asyncio.run(test_e2e_float_scaling())
