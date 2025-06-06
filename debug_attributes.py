"""
Quick debug script to check the output object attributes
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import asyncio
from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def debug_attributes():
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(sample_size=100)
      # Try to find a single trade-up
    results = await finder.find_profitable_trades(
        min_profit=-100.0,
        max_input_price=None,
        limit=1
    )
    
    if results:
        result = results[0]
        print("🔍 Debugging Output Attributes:")
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
    else:
        print("No results found")

if __name__ == "__main__":
    asyncio.run(debug_attributes())
