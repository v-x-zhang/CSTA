"""
Investigate pricing data quality to understand why consumer grade skins
are priced so much higher than their outputs, making all trade-ups unprofitable.
"""

import asyncio
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.logging_config import setup_logging

async def investigate_pricing():
    """Investigate pricing data quality issues"""
    
    setup_logging(level='INFO')
    print("💰 PRICING DATA QUALITY INVESTIGATION")
    print("=" * 60)
    
    # Initialize system
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(use_all_prices=True)
    
    # Get The Ancient Collection for analysis
    ancient_collection = finder.market_data.collections.get('The Ancient Collection')
    if not ancient_collection:
        print("❌ Ancient Collection not found")
        return
    
    print(f"📊 Analyzing: {ancient_collection.name}")
    
    # Analyze Consumer Grade pricing
    consumer_skins = ancient_collection.skins_by_rarity.get('Consumer Grade', [])
    industrial_skins = ancient_collection.skins_by_rarity.get('Industrial Grade', [])
    
    print(f"\n🔍 CONSUMER GRADE ANALYSIS ({len(consumer_skins)} skins)")
    consumer_prices = []
    
    for skin in consumer_skins[:10]:  # Look at first 10
        price = finder._cached_prices.get(skin.name, 0)
        consumer_prices.append(price)
        print(f"   {skin.name}: ${price:.2f}")
    
    if consumer_prices:
        avg_consumer = sum(consumer_prices) / len(consumer_prices)
        min_consumer = min(consumer_prices)
        max_consumer = max(consumer_prices)
        print(f"   Consumer Average: ${avg_consumer:.2f}")
        print(f"   Consumer Range: ${min_consumer:.2f} - ${max_consumer:.2f}")
    
    print(f"\n🔍 INDUSTRIAL GRADE ANALYSIS ({len(industrial_skins)} skins)")
    industrial_prices = []
    
    for skin in industrial_skins[:10]:
        price = finder._cached_prices.get(skin.name, 0)
        industrial_prices.append(price)
        print(f"   {skin.name}: ${price:.2f}")
    
    if industrial_prices:
        avg_industrial = sum(industrial_prices) / len(industrial_prices)
        min_industrial = min(industrial_prices)
        max_industrial = max(industrial_prices)
        print(f"   Industrial Average: ${avg_industrial:.2f}")
        print(f"   Industrial Range: ${min_industrial:.2f} - ${max_industrial:.2f}")
    
    # Calculate theoretical trade-up profitability
    print(f"\n📈 TRADE-UP PROFITABILITY ANALYSIS")
    
    if consumer_prices and industrial_prices:
        min_input_cost = min_consumer * 10  # 10 cheapest consumer skins
        avg_input_cost = avg_consumer * 10  # 10 average consumer skins
        max_output_value = max_industrial    # Best possible output
        avg_output_value = avg_industrial    # Average output
        
        print(f"   Minimum Input Cost (10x cheapest): ${min_input_cost:.2f}")
        print(f"   Average Input Cost (10x average): ${avg_input_cost:.2f}")
        print(f"   Maximum Output Value (best): ${max_output_value:.2f}")
        print(f"   Average Output Value: ${avg_output_value:.2f}")
        
        best_case_profit = max_output_value - min_input_cost
        avg_case_profit = avg_output_value - avg_input_cost
        
        print(f"   Best Case Profit: ${best_case_profit:.2f}")
        print(f"   Average Case Profit: ${avg_case_profit:.2f}")
        
        if best_case_profit < -10:
            print(f"   ❌ Even BEST case loses more than $10!")
        elif avg_case_profit < -10:
            print(f"   ⚠️  Average case loses more than $10")
        else:
            print(f"   ✅ Some trades might be viable")
    
    # Check other collections for comparison
    print(f"\n🔍 COMPARING OTHER COLLECTIONS")
    
    viable_collections = 0
    total_checked = 0
    
    for collection_name, collection in list(finder.market_data.collections.items())[:5]:
        total_checked += 1
        consumer_skins = collection.skins_by_rarity.get('Consumer Grade', [])
        industrial_skins = collection.skins_by_rarity.get('Industrial Grade', [])
        
        if len(consumer_skins) >= 10 and len(industrial_skins) >= 1:
            # Quick viability check
            consumer_sample = [finder._cached_prices.get(skin.name, 0) for skin in consumer_skins[:10]]
            industrial_sample = [finder._cached_prices.get(skin.name, 0) for skin in industrial_skins[:5]]
            
            if consumer_sample and industrial_sample:
                min_input = min(consumer_sample) * 10
                max_output = max(industrial_sample)
                profit = max_output - min_input
                
                print(f"   {collection_name}:")
                print(f"     Min input cost: ${min_input:.2f}")
                print(f"     Max output value: ${max_output:.2f}")
                print(f"     Best profit: ${profit:.2f}")
                
                if profit > -10:
                    viable_collections += 1
                    print(f"     ✅ Potentially viable")
                else:
                    print(f"     ❌ Not viable (loses ${abs(profit):.2f})")
    
    print(f"\n📊 SUMMARY")
    print(f"   Collections checked: {total_checked}")
    print(f"   Potentially viable: {viable_collections}")
    print(f"   Viability rate: {viable_collections/total_checked*100:.1f}%")
    
    # Check if this is a data source issue
    print(f"\n🔍 DATA SOURCE INVESTIGATION")
    
    # Look for patterns in skin names that might indicate pricing issues
    sample_skins = []
    for collection in list(finder.market_data.collections.values())[:3]:
        for rarity_skins in collection.skins_by_rarity.values():
            sample_skins.extend(rarity_skins[:2])
    
    print(f"   Sample skin name formats:")
    for skin in sample_skins[:10]:
        price = finder._cached_prices.get(skin.name, 0)
        print(f"     '{skin.name}' → ${price:.2f}")
    
    # Check for suspicious pricing patterns
    all_prices = list(finder._cached_prices.values())
    prices_over_100 = sum(1 for p in all_prices if p > 100)
    prices_under_5 = sum(1 for p in all_prices if p < 5)
    
    print(f"\n   Pricing distribution:")
    print(f"     Prices > $100: {prices_over_100:,} ({prices_over_100/len(all_prices)*100:.1f}%)")
    print(f"     Prices < $5: {prices_under_5:,} ({prices_under_5/len(all_prices)*100:.1f}%)")
    print(f"     Total prices: {len(all_prices):,}")
    
    if prices_over_100 > len(all_prices) * 0.3:
        print(f"   ⚠️  WARNING: {prices_over_100/len(all_prices)*100:.1f}% of prices are > $100")
        print(f"      This suggests possible data quality issues")

if __name__ == "__main__":
    asyncio.run(investigate_pricing())
