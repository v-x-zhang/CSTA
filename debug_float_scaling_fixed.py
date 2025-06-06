"""
Test the fixed float scaling calculation using real skin data with proper input ranges
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.steam_pricing import SteamPricingClient

async def test_fixed_float_scaling():
    """Test the float scaling with real skin data to verify the fix"""
    
    print("🧪 Testing Fixed Float Scaling with Real Skin Data")
    print("=" * 60)
    
    # Initialize the finder with Steam pricing
    finder = ComprehensiveTradeUpFinder(use_steam_pricing=True)
    await finder.initialize(sample_size=50)
    
    print("✅ Initialized trade-up finder with Steam pricing")
      # Test case: Find a real trade-up to test with actual skin data
    print("\n🔍 Finding a real trade-up opportunity...")
    
    # Get input skins for the collection
    input_skins = finder.db_manager.get_skins_by_collection_and_rarity(
        "The 2021 Dust 2 Collection", "Consumer Grade"
    )
    
    if not input_skins:
        print("❌ No input skins found for The 2021 Dust 2 Collection")
        return
    
    result = await finder._calculate_single_collection_tradeup(
        collection="The 2021 Dust 2 Collection",
        input_rarity="Consumer Grade",
        input_skins=input_skins,
        max_input_price=5.0,
        min_profit=0.0  # Any profit
    )
    
    if result:
        print(f"✅ Found trade-up opportunity in {result.input_config.collection1}")
        print(f"📊 Input: {result.input_config.skins[0].name}")
        print(f"💰 Input cost: ${result.input_config.total_cost:.2f}")
        print(f"📈 Expected profit: ${result.raw_profit:.2f}")
        
        print(f"\n🎯 Output Possibilities ({len(result.output_skins)} skins):")
        for i, output in enumerate(result.output_skins[:3], 1):  # Show first 3
            print(f"  {i}. {output.skin.name}")
            print(f"     Price: ${output.skin.price:.2f}")
            print(f"     Probability: {output.probability:.1%}")
            if hasattr(output, 'predicted_float'):
                print(f"     Predicted Float: {output.predicted_float:.6f}")
            if hasattr(output, 'predicted_condition'):
                print(f"     Predicted Condition: {output.predicted_condition}")
            print()
        
        # Test the float scaling method directly with the input/output data
        print("🔬 Direct Float Scaling Test:")
        print("-" * 40)
        
        # Get the actual input skin data
        input_skin_name = result.input_config.skins[0].name
        print(f"Input skin: {input_skin_name}")
        
        # We need to get the actual skin data from the database
        input_skins = finder.db_manager.get_skins_by_collection_and_rarity(
            "The 2021 Dust 2 Collection", "Consumer Grade"
        )
        output_skins = finder.db_manager.get_skins_by_collection_and_rarity(
            "The 2021 Dust 2 Collection", "Industrial Grade"
        )
        
        # Find the specific input and output skins
        input_skin_data = None
        for skin in input_skins:
            if skin['market_hash_name'] in input_skin_name:
                input_skin_data = skin
                break
        
        if input_skin_data and output_skins:
            print(f"✅ Found input skin data: {input_skin_data['market_hash_name']}")
            print(f"   Float range: {input_skin_data.get('min_float', 'N/A')} - {input_skin_data.get('max_float', 'N/A')}")
            
            # Test with Field-Tested condition (midpoint)
            input_float = 0.265  # Field-Tested midpoint
            
            print(f"\n📋 Testing with input float: {input_float} (Field-Tested)")
            
            for i, output_skin in enumerate(output_skins[:3], 1):
                print(f"\n{i}. Output: {output_skin['market_hash_name']}")
                print(f"   Range: {output_skin.get('min_float', 0.0):.3f} - {output_skin.get('max_float', 1.0):.3f}")
                
                # Test with old method (hardcoded range)
                old_scaled_float, old_condition = finder._calculate_output_float_and_condition(
                    input_float, output_skin
                )
                
                # Test with new method (proper input skin range)
                new_scaled_float, new_condition = finder._calculate_output_float_and_condition(
                    input_float, output_skin, input_skin_data
                )
                
                print(f"   Old method (hardcoded): {old_scaled_float:.6f} ({old_condition})")
                print(f"   New method (real skin): {new_scaled_float:.6f} ({new_condition})")
                
                if abs(old_scaled_float - new_scaled_float) > 0.001:
                    print(f"   ⚠️  Difference: {abs(old_scaled_float - new_scaled_float):.6f}")
                else:
                    print(f"   ✅ Similar results (difference: {abs(old_scaled_float - new_scaled_float):.6f})")
    else:
        print("❌ No trade-up opportunity found")
        
        # Test the method directly with mock data
        print("\n🧪 Testing with mock skin data:")
        
        # Create mock input skin with specific range
        mock_input_skin = {
            'market_hash_name': 'Test Input Skin',
            'min_float': 0.0,
            'max_float': 0.8
        }
        
        # Create mock output skin
        mock_output_skin = {
            'market_hash_name': 'Test Output Skin',
            'min_float': 0.15,
            'max_float': 0.38
        }
        
        input_float = 0.16  # Just above minimum for input
        
        # Test with old method (hardcoded)
        old_result = finder._calculate_output_float_and_condition(input_float, mock_output_skin)
        
        # Test with new method (proper input range)
        new_result = finder._calculate_output_float_and_condition(input_float, mock_output_skin, mock_input_skin)
        
        print(f"Input float: {input_float}")
        print(f"Input range: {mock_input_skin['min_float']} - {mock_input_skin['max_float']}")
        print(f"Output range: {mock_output_skin['min_float']} - {mock_output_skin['max_float']}")
        print(f"Old method: {old_result[0]:.6f} ({old_result[1]})")
        print(f"New method: {new_result[0]:.6f} ({new_result[1]})")

if __name__ == "__main__":
    asyncio.run(test_fixed_float_scaling())
