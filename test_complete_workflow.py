"""
Test script to verify the complete workflow:
1. Load all pricing data
2. Test float scaling with specific inputs
3. Validate trade-up calculation end-to-end
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.logging_config import setup_logging

async def test_complete_workflow():
    """Test the complete workflow with all pricing data"""
    
    setup_logging(level='INFO')
    print("🧪 Testing Complete Workflow with Full Pricing Data")
    print("=" * 60)
    
    # Initialize with all pricing data
    finder = ComprehensiveTradeUpFinder()
    print("📊 Loading ALL pricing data...")
    await finder.initialize(use_all_prices=True)
    
    # Get market summary
    summary = finder.get_market_summary()
    print(f"\n✅ Loaded {summary.get('cached_prices', 0):,} prices")
    print(f"✅ {summary.get('total_skins', 0):,} total skins in database")
    print(f"✅ {summary.get('unique_collections', 0):,} collections available")
    
    # Test specific float scaling scenario
    print("\n🔬 Testing Float Scaling...")
    
    # Look for AK-47 Redline (Field-Tested) in Industrial Grade
    target_weapon = "AK-47"
    target_skin = "Redline"
    
    # Search through market data to find this skin
    redline_skin = None
    for collection_data in finder.market_data.collections.values():
        for rarity_list in collection_data.skins_by_rarity.values():
            for skin in rarity_list:
                if target_weapon in skin.name and target_skin in skin.name:
                    redline_skin = skin
                    break
            if redline_skin:
                break
        if redline_skin:
            break    
    if redline_skin:
        print(f"🎯 Found: {redline_skin.name}")
        print(f"   Float Range: {redline_skin.float_min} - {redline_skin.float_max}")
          # Test float scaling
        input_float = 0.265  # Field-Tested midpoint
        
        # Convert Skin object to expected dictionary format
        output_skin_dict = {
            'market_hash_name': redline_skin.name,
            'min_float': redline_skin.float_min,
            'max_float': redline_skin.float_max
        }
        
        scaled_result = finder._calculate_output_float_and_condition(
            input_float, output_skin_dict
        )
        
        if scaled_result:
            scaled_float, predicted_condition = scaled_result
            print(f"   Input Float: {input_float} (Field-Tested)")
            print(f"   Scaled Float: {scaled_float:.6f}")
            print(f"   Predicted Condition: {predicted_condition}")
            
            # Validate the scaling
            expected_range_position = (input_float - 0.15) / (0.38 - 0.15)  # FT range
            expected_output = redline_skin.float_min + (expected_range_position * (redline_skin.float_max - redline_skin.float_min))
            print(f"   Expected Float: {expected_output:.6f}")
            print(f"   ✅ Scaling {'CORRECT' if abs(scaled_float - expected_output) < 0.000001 else 'INCORRECT'}")
    else:
        print("❌ Could not find AK-47 Redline in market data")
    
    # Try to find at least one profitable trade-up
    print(f"\n🔍 Searching for ANY profitable trade-up...")
    results = await finder.find_profitable_trades(
        min_profit=0.01,  # Very low threshold
        limit=1
    )
    
    if results:
        result = results[0]
        print("✅ Found profitable trade-up!")
        print(f"   Expected Profit: ${result.expected_profit:.2f}")
        print(f"   Total Cost: ${result.total_cost:.2f}")
        print(f"   Expected Value: ${result.expected_value:.2f}")
        
        # Show input skins
        print("   Input Skins:")
        for input_skin in result.input_skins:
            print(f"     - {input_skin.name} x{input_skin.quantity} @ ${input_skin.price:.2f}")
            
        # Show possible outputs with float predictions
        print("   Possible Outputs:")
        for output in result.possible_outcomes:
            if hasattr(output, 'predicted_float') and hasattr(output, 'predicted_condition'):
                print(f"     - {output.name} (Float: {output.predicted_float:.4f}, {output.predicted_condition}) - {output.probability:.1%} chance")
            else:
                print(f"     - {output.name} - {output.probability:.1%} chance")
                
    else:
        print("❌ No profitable trade-ups found")
        
        # Let's check if there are any trade-ups at all (even unprofitable)
        print("\n🔍 Checking for ANY trade-ups (profit/loss doesn't matter)...")
        
        # Manual check - look at first collection and try to find any valid trade-up inputs
        first_collection = list(finder.market_data.collections.values())[0]
        print(f"   Checking collection: {first_collection.name}")
        
        # Check if we have enough pricing data for consumer grade skins
        consumer_skins = first_collection.skins_by_rarity.get('Consumer Grade', [])
        priced_consumer = [skin for skin in consumer_skins if skin.name in finder._cached_prices]
        print(f"   Consumer skins with prices: {len(priced_consumer)}/{len(consumer_skins)}")
        
        if len(priced_consumer) >= 10:  # Need 10 for trade-up
            print("   ✅ Sufficient consumer skins with pricing data")
        else:
            print("   ❌ Insufficient consumer skins with pricing data")

    print("\n" + "=" * 60)
    print("🏁 Workflow Test Complete")

if __name__ == "__main__":
    asyncio.run(test_complete_workflow())
