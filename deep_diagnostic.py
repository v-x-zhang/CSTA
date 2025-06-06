"""
Deep diagnostic script to identify why NO trade-ups are being found,
even with -$10 minimum profit threshold.

This will systematically check:
1. Input skin availability and pricing
2. Collection structure and mappings
3. Output skin availability and pricing
4. Trade-up validation logic
5. Any blocking conditions in the pipeline
"""

import asyncio
import sys
from pathlib import Path
from collections import defaultdict

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
from src.logging_config import setup_logging

async def deep_diagnostic():
    """Perform deep diagnostic to find why no trade-ups are discovered"""
    
    setup_logging(level='INFO')
    print("🔍 DEEP DIAGNOSTIC: Why No Trade-ups Are Found")
    print("=" * 60)
    
    # Initialize system
    finder = ComprehensiveTradeUpFinder()
    await finder.initialize(use_all_prices=True)
    
    summary = finder.get_market_summary()
    print(f"📊 System Status:")
    print(f"   Loaded Prices: {summary.get('cached_prices', 0):,}")
    print(f"   Total Skins: {summary.get('total_skins', 0):,}")
    print(f"   Collections: {summary.get('unique_collections', 0):,}")
    
    # Check 1: Basic data structure
    print(f"\n🔍 Check 1: Basic Data Structure")
    print(f"   Market Data Object: {'✅ EXISTS' if finder.market_data else '❌ MISSING'}")
    print(f"   Collections: {len(finder.market_data.collections) if finder.market_data else 0}")
    print(f"   Cached Prices: {len(finder._cached_prices)}")
    
    if not finder.market_data or not finder.market_data.collections:
        print("❌ CRITICAL: No market data or collections found!")
        return
    
    # Check 2: Examine first collection in detail
    print(f"\n🔍 Check 2: Collection Structure Analysis")
    first_collection_name = list(finder.market_data.collections.keys())[0]
    first_collection = finder.market_data.collections[first_collection_name]
    
    print(f"   First Collection: {first_collection.name}")
    print(f"   Rarity Levels: {list(first_collection.skins_by_rarity.keys())}")
    
    for rarity, skins in first_collection.skins_by_rarity.items():
        print(f"   {rarity}: {len(skins)} skins")
        
        # Check pricing coverage for this rarity
        priced_skins = 0
        total_skins = len(skins)
        
        for skin in skins[:5]:  # Check first 5 skins
            if skin.name in finder._cached_prices:
                priced_skins += 1
                print(f"     ✅ {skin.name} - ${finder._cached_prices[skin.name]:.2f}")
            else:
                print(f"     ❌ {skin.name} - NO PRICE")
        
        if total_skins > 5:
            print(f"     ... and {total_skins - 5} more skins")
        
        print(f"   Pricing Coverage: {priced_skins}/{min(5, total_skins)} checked")
    
    # Check 3: Look for Consumer Grade specifically
    print(f"\n🔍 Check 3: Consumer Grade Analysis (Required for Trade-ups)")
    consumer_collections = 0
    total_consumer_skins = 0
    priced_consumer_skins = 0
    
    for collection_name, collection in finder.market_data.collections.items():
        consumer_skins = collection.skins_by_rarity.get('Consumer Grade', [])
        if consumer_skins:
            consumer_collections += 1
            total_consumer_skins += len(consumer_skins)
            
            collection_priced = sum(1 for skin in consumer_skins if skin.name in finder._cached_prices)
            priced_consumer_skins += collection_priced
            
            print(f"   {collection_name}: {len(consumer_skins)} consumer skins, {collection_priced} priced")
    
    print(f"   Total Collections with Consumer Grade: {consumer_collections}")
    print(f"   Total Consumer Skins: {total_consumer_skins}")
    print(f"   Priced Consumer Skins: {priced_consumer_skins}")
    
    if priced_consumer_skins < 10:
        print("❌ CRITICAL: Not enough priced consumer skins for any trade-ups!")
        print("   Trade-ups require 10 input skins of the same rarity.")
        return
    
    # Check 4: Manual trade-up attempt
    print(f"\n🔍 Check 4: Manual Trade-up Attempt")
    
    # Find a collection with sufficient consumer skins
    suitable_collection = None
    for collection_name, collection in finder.market_data.collections.items():
        consumer_skins = collection.skins_by_rarity.get('Consumer Grade', [])
        priced_consumer = [skin for skin in consumer_skins if skin.name in finder._cached_prices]
        
        if len(priced_consumer) >= 10:
            suitable_collection = collection
            print(f"   Found suitable collection: {collection_name}")
            print(f"   Consumer skins with prices: {len(priced_consumer)}")
            break
    
    if not suitable_collection:
        print("❌ No collection has 10+ priced consumer skins for trade-up")
        return
    
    # Check possible outputs
    industrial_skins = suitable_collection.skins_by_rarity.get('Industrial Grade', [])
    priced_industrial = [skin for skin in industrial_skins if skin.name in finder._cached_prices]
    
    print(f"   Possible outputs (Industrial Grade): {len(industrial_skins)} total, {len(priced_industrial)} priced")
    
    if not priced_industrial:
        print("❌ No priced Industrial Grade outputs for this collection")
        return
    
    # Check 5: Specific validation issues
    print(f"\n🔍 Check 5: Validation Logic Issues")
    
    # Try calling the internal method directly
    try:
        consumer_skins = suitable_collection.skins_by_rarity.get('Consumer Grade', [])
        priced_consumer = [skin for skin in consumer_skins if skin.name in finder._cached_prices]
        
        print(f"   Testing with collection: {suitable_collection.name}")
        print(f"   Available consumer skins: {len(priced_consumer)}")
        
        # Get first 10 consumer skins for testing
        test_inputs = priced_consumer[:10]
        print(f"   Test input skins:")
        for i, skin in enumerate(test_inputs):
            price = finder._cached_prices.get(skin.name, 0)
            print(f"     {i+1}. {skin.name} - ${price:.2f}")
        
        total_cost = sum(finder._cached_prices.get(skin.name, 0) for skin in test_inputs)
        print(f"   Total cost: ${total_cost:.2f}")
        
        if total_cost == 0:
            print("❌ CRITICAL: All input skins have $0.00 price!")
            
        # Check outputs
        print(f"   Possible outputs:")
        for skin in priced_industrial[:5]:
            price = finder._cached_prices.get(skin.name, 0)
            print(f"     - {skin.name} - ${price:.2f}")
        
    except Exception as e:
        print(f"❌ Error in manual validation: {e}")
        import traceback
        traceback.print_exc()
    
    # Check 6: Price validation logic
    print(f"\n🔍 Check 6: Price Validation Details")
    
    # Check if there are any $0 prices that might be blocking
    zero_prices = sum(1 for price in finder._cached_prices.values() if price == 0)
    total_prices = len(finder._cached_prices)
    
    print(f"   Total prices: {total_prices}")
    print(f"   Zero prices: {zero_prices}")
    print(f"   Valid prices: {total_prices - zero_prices}")
    
    if zero_prices > total_prices * 0.5:
        print("⚠️  WARNING: More than 50% of prices are $0.00")
    
    # Check price ranges
    valid_prices = [price for price in finder._cached_prices.values() if price > 0]
    if valid_prices:
        min_price = min(valid_prices)
        max_price = max(valid_prices)
        avg_price = sum(valid_prices) / len(valid_prices)
        print(f"   Price range: ${min_price:.2f} - ${max_price:.2f}")
        print(f"   Average price: ${avg_price:.2f}")
    
    print(f"\n🎯 DIAGNOSTIC COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(deep_diagnostic())
