#!/usr/bin/env python3
"""Test the fixed comprehensive trade finder"""

import asyncio
import sys
import os
import argparse

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from comprehensive_trade_finder import ComprehensiveTradeUpFinder

async def main(stop_after_one=False):
    try:
        print("Initializing comprehensive trade finder...")
        finder = ComprehensiveTradeUpFinder()
        await finder.initialize(sample_size=100)
        
        print("Testing updated trade finder with proper CS:GO trade-up rules...")
        
        # Find some profitable trades
        limit = 1 if stop_after_one else 3
        trades = await finder.find_profitable_trades(min_profit=0.1, limit=limit)
        
        print(f"\nFound {len(trades)} trade opportunities")
        
        if stop_after_one and len(trades) > 0:
            print("Stopping after finding first profitable trade-up as requested.")
        
        for i, trade in enumerate(trades):
            print(f"\n=== Trade {i+1} ===")
            print(f"Input Collection: {trade.input_config.collection1}")
            if trade.input_config.collection2:
                print(f"Secondary Collection: {trade.input_config.collection2}")
                print(f"Split Ratio: {trade.input_config.split_ratio}")
            
            print(f"Total Input Cost: ${trade.input_config.total_cost:.2f}")
            print(f"Expected Output Value: ${trade.expected_output_price:.2f}")
            print(f"Expected Profit: ${trade.raw_profit:.2f}")
            print(f"ROI: {trade.roi_percentage:.1f}%")
            print(f"Number of Possible Outputs: {len(trade.output_skins)}")
            
            print("\nTop Output Possibilities:")
            # Sort outputs by probability
            sorted_outputs = sorted(trade.output_skins, key=lambda x: x.probability, reverse=True)
            for j, output in enumerate(sorted_outputs[:3]):
                print(f"  {j+1}. {output.skin.name}")
                print(f"     Probability: {output.probability:.3f} ({output.probability*100:.1f}%)")
                print(f"     Price: ${output.skin.price:.2f}")
                print(f"     Collection: {output.skin.collection}")
        
        print("\n=== Test Complete ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test comprehensive trade finder')
    parser.add_argument('--stop-after-one', action='store_true', 
                       help='Stop after finding just one profitable trade-up')
    args = parser.parse_args()
    
    asyncio.run(main(stop_after_one=args.stop_after_one))
