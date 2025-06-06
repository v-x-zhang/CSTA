"""
Simple pricing debug
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.runtime_pricing import RuntimePricingClient

async def simple_pricing_debug():
    print("Testing pricing client directly...")
    
    try:
        client = RuntimePricingClient()
        print("Created pricing client")
        
        # Try to get sample prices
        sample_prices = await client.get_sample_prices(limit=10)
        print(f"Got {len(sample_prices)} sample prices:")
        
        for name, price in list(sample_prices.items())[:5]:
            print(f"  {name}: ${price}")
            
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(simple_pricing_debug())
