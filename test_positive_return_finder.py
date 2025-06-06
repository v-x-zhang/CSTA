"""
Test script for the positive expected return trade-up finder with CSFloat validation
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from comprehensive_trade_finder import ComprehensiveTradeUpFinder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_positive_return_finder():
    """Test the positive expected return finder with CSFloat validation"""
    print("=" * 80)
    print("CS:GO Trade-up Analysis - Positive Expected Return Finder")
    print("=" * 80)
    
    try:
        # Initialize the finder
        finder = ComprehensiveTradeUpFinder()
        await finder.initialize(sample_size=2000)  # Use more samples for better accuracy
        
        print("\n🔍 Searching for trade-ups with positive expected return...")
        print("This will find the first opportunity and validate it with real CSFloat data.")
        print("-" * 60)
        
        # Find positive return trade-up with CSFloat validation
        result = await finder.find_positive_return_with_csfloat_validation(
            max_input_cost=50.0,  # Maximum cost per input item
            min_expected_return=0.1,  # Minimum 10 cents expected profit
            max_rarities_to_check=3  # Check Consumer, Industrial, Mil-Spec
        )
        
        if result:
            print("\n✅ POSITIVE EXPECTED RETURN TRADE-UP FOUND!")
            print("=" * 60)
            
            # Display the comprehensive results
            print(f"📊 Trade-up Collection: {result['collection']}")
            print(f"🎯 Input Rarity: {result['input_rarity']}")
            print(f"🎁 Output Rarity: {result['output_rarity']}")
            print()
            
            # Financial Summary
            financial = result['financial_analysis']
            print("💰 FINANCIAL ANALYSIS")
            print("-" * 30)
            print(f"Total Input Cost: ${financial['total_input_cost']:.2f}")
            print(f"Expected Output Value: ${financial['expected_output_value']:.2f}")
            print(f"Steam Fees (15%): ${financial['steam_fees']:.2f}")
            print(f"Expected Return: ${financial['expected_return']:.2f}")
            print(f"Return Percentage: {financial['return_percentage']:.1f}%")
            print()
            
            # Float Analysis
            float_analysis = result['float_analysis']
            print("🎲 FLOAT ANALYSIS")
            print("-" * 20)
            print(f"Input Items Scaled Float Average: {float_analysis['scaled_average']:.6f}")
            print(f"Expected Output Float: {float_analysis['output_float']:.6f}")
            print(f"Expected Output Condition: {float_analysis['output_condition']}")
            print()
            
            # Purchase Instructions
            purchase_info = result['purchase_instructions']
            print("🛒 PURCHASE INSTRUCTIONS")
            print("-" * 30)
            for i, item in enumerate(purchase_info['items'], 1):
                print(f"\n{i}. {item['skin_name']}")
                print(f"   Float: {item['float']:.6f} ({item['condition']})")
                print(f"   Price: ${item['price']:.2f}")
                print(f"   Seller: {item['seller']}")
                print(f"   URL: {item['purchase_url']}")
            
            print()
            print("📝 SUMMARY")
            print("-" * 10)
            print(f"• Buy {len(purchase_info['items'])} items for ${financial['total_input_cost']:.2f}")
            print(f"• Trade them up to get an item worth ~${financial['expected_output_value']:.2f}")
            print(f"• After Steam fees, expect ~${financial['expected_return']:.2f} profit")
            print(f"• This represents a {financial['return_percentage']:.1f}% return on investment")
            
        else:
            print("\n❌ No positive expected return trade-ups found")
            print("This could be due to:")
            print("• Current market conditions")
            print("• Limited sample size")
            print("• High competition in the market")
            print("• Try adjusting the search parameters")
            
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_positive_return_finder())
