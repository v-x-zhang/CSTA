"""
Test the comprehensive trade finder with CSFloat validation for positive expected return trade-ups
"""

import sys
import os
import asyncio
import json
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.logging_config import setup_logging

async def main():
    print("=" * 80)
    print("CS:GO Trade-Up Analysis - Positive Expected Return Finder")
    print("Using CSFloat API for Real-Time Validation")
    print("=" * 80)
    print()
    
    # Setup logging
    setup_logging()
    
    # Initialize the comprehensive finder
    print("🔧 Initializing comprehensive trade finder...")
    finder = ComprehensiveTradeUpFinder()
    
    try:
        # Initialize with sample data
        print("📊 Loading sample market data...")
        await finder.initialize(sample_size=2000)
        print("✅ Initialization complete!")
        print()
        
        # Find positive expected return trade-ups with CSFloat validation
        print("🔍 Searching for positive expected return trade-ups...")
        print("   • Looking for any trade-up with expected profit > $0")
        print("   • Will validate first opportunity with real CSFloat data")
        print("   • This may take a few minutes...")
        print()
        
        start_time = datetime.now()
        
        result = await finder.find_positive_return_with_csfloat_validation(
            selling_fee_rate=0.15,  # 15% Steam market fee
            target_collections=None  # Search all collections
        )
        
        end_time = datetime.now()
        elapsed = (end_time - start_time).total_seconds()
        
        print(f"⏱️  Search completed in {elapsed:.1f} seconds")
        print()
        
        if result:
            print("🎉 PROFITABLE TRADE-UP FOUND!")
            print("=" * 60)
            
            # Display comprehensive results
            display_trade_up_analysis(result)
            
        else:
            print("❌ No profitable trade-ups found")
            print("   • All analyzed opportunities had negative expected returns")
            print("   • Market conditions may not be favorable currently")
            print("   • Try again later or adjust search parameters")
        
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await finder.close()
        print("\n🔄 Analysis complete!")

def display_trade_up_analysis(result):
    """Display comprehensive trade-up analysis results"""
    
    print(f"📋 Trade Type: {result['trade_type']}")
    print(f"📦 Input Collection: {result['input_collection']}")
    print(f"📈 {result['input_rarity']} → {result['output_rarity']}")
    print()
    
    # Financial Summary
    print("💰 FINANCIAL ANALYSIS")
    print("-" * 40)
    financial = result['financial_summary']
    print(f"Total Input Cost:     ${financial['total_input_cost']:.2f}")
    print(f"Expected Output:      ${financial['expected_output_value']:.2f}")
    print(f"After Selling Fees:   ${financial['net_expected_value_after_fees']:.2f}")
    print(f"Expected Profit:      ${financial['expected_profit']:.2f}")
    print(f"ROI:                  {financial['roi_percentage']:.1f}%")
    print(f"Selling Fee Rate:     {financial['selling_fee_rate']*100:.0f}%")
    print()
    
    # Input Item Details
    print("🛒 PURCHASE REQUIREMENTS")
    print("-" * 40)
    input_info = result['input_skin']
    print(f"Item: {input_info['name']}")
    print(f"Quantity: {input_info['quantity_needed']} items")
    print(f"Platform: {result['purchase_instructions']['platform']}")
    print()
    
    # Purchase Plan
    purchase_info = input_info['purchase_info']
    if purchase_info['available']:
        print("📋 PURCHASE PLAN:")
        for i, item in enumerate(purchase_info['purchase_plan'], 1):
            print(f"  {i:2d}. ${item['price']:.2f} - Float: {item['float']:.4f} - Seller: {item['seller']}")
            print(f"      URL: {item['url']}")
        print(f"\nTotal Cost: ${purchase_info['total_cost']:.2f}")
    else:
        print("❌ Not enough items available for purchase")
    print()
    
    # Float Analysis
    print("🎯 FLOAT ANALYSIS")
    print("-" * 40)
    float_info = result['float_analysis']
    print(f"Input Floats: {', '.join(f'{f:.4f}' for f in float_info['input_floats'])}")
    print(f"Average Input Float: {float_info['average_input_float']:.4f}")
    print(f"Scaled Average: {float_info['scaled_average_float']:.4f}")
    print(f"Wear Conditions: {', '.join(set(float_info['input_wear_conditions']))}")
    print()
    
    # Output Possibilities
    print("🎲 POSSIBLE OUTPUTS")
    print("-" * 40)
    for i, output in enumerate(result['output_possibilities'], 1):
        print(f"{i}. {output['name']}")
        print(f"   Probability: {output['probability']*100:.1f}%")
        print(f"   CSFloat Price: ${output['csfloat_price']:.2f}")
        print(f"   Expected Float: {output['expected_float']:.4f} ({output['wear_condition']})")
        print(f"   Sample Listings:")
        for j, listing in enumerate(output['listings'], 1):
            print(f"     {j}. ${listing['price']:.2f} - Float: {listing['float']:.4f}")
        print()
    
    # Instructions
    print("📝 EXECUTION INSTRUCTIONS")
    print("-" * 40)
    instructions = result['purchase_instructions']
    print(f"1. Visit {instructions['platform']} marketplace")
    print(f"2. Purchase {instructions['total_items_needed']} items as listed above")
    print(f"3. Execute trade-up contract in CS:GO")
    print(f"4. Sell output on Steam Community Market")
    print(f"5. Estimated time: {instructions['estimated_completion_time']}")
    print()
    
    print("⚠️  IMPORTANT NOTES:")
    print("• Prices are real-time and may change")
    print("• Market fees reduce final profit")
    print("• Trade-up outcomes are probabilistic")
    print("• Float values affect final item condition")

if __name__ == "__main__":
    asyncio.run(main())
