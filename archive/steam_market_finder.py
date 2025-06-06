#!/usr/bin/env python3
"""
Steam Market Trade-Up Finder for CS2
Uses free Steam Market API to find profitable trade-up opportunities
This is a working demo version using available free APIs
"""

import json
import requests
import time
import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import urllib.parse

@dataclass
class MarketListing:
    """Represents a skin listing on Steam Market"""
    item_name: str
    market_name: str
    price_usd: float
    float_value: float
    market_url: str
    rarity: str
    collection: str
    wear: str

@dataclass
class TradeUpOpportunity:
    """Represents a profitable trade-up opportunity"""
    input_items: List[MarketListing]
    total_cost: float
    expected_output_value: float
    estimated_profit: float
    profit_percentage: float
    output_rarity: str

class SteamMarketTradeUpFinder:
    def __init__(self):
        self.base_url = "https://steamcommunity.com/market"
        
        # CS2 rarity progression for trade-ups
        self.rarity_progression = {
            "Consumer Grade": "Industrial Grade",
            "Industrial Grade": "Mil-Spec Grade",
            "Mil-Spec Grade": "Restricted",
            "Restricted": "Classified",
            "Classified": "Covert"
        }
        
        # Steam market fee: 15% total (10% to Steam, 5% to game)
        self.steam_fee_rate = 0.15
        
        # Sample CS2 items for demonstration
        self.sample_items = {
            "Mil-Spec Grade": [
                ("AK-47 | Blue Laminate (Field-Tested)", "Dust 2 Collection"),
                ("M4A4 | Faded Zebra (Field-Tested)", "Dust 2 Collection"),
                ("USP-S | Dark Water (Field-Tested)", "Dust Collection"),
                ("Glock-18 | Blue Fissure (Field-Tested)", "Dust Collection"),
                ("P250 | Bone Mask (Field-Tested)", "Dust Collection"),
                ("MP7 | Anodized Navy (Field-Tested)", "Dust Collection"),
                ("UMP-45 | Indigo (Field-Tested)", "Dust Collection"),
                ("P90 | Sand Spray (Field-Tested)", "Dust Collection"),
                ("Nova | Polar Mesh (Field-Tested)", "Dust Collection"),
                ("XM1014 | Blue Steel (Field-Tested)", "Dust Collection"),
                ("FAMAS | Colony (Field-Tested)", "Dust 2 Collection"),
                ("Galil AR | Sage Spray (Field-Tested)", "Dust 2 Collection"),
            ],
            "Industrial Grade": [
                ("MAC-10 | Silver (Field-Tested)", "Dust Collection"),
                ("MP9 | Hot Rod (Factory New)", "Dust Collection"),
                ("Five-SeveN | Orange Peel (Field-Tested)", "Dust Collection"),
                ("SG 553 | Waves Perforated (Field-Tested)", "Dust Collection"),
                ("SSG 08 | Blue Spruce (Field-Tested)", "Dust Collection"),
                ("Dual Berettas | Colony (Field-Tested)", "Dust 2 Collection"),
                ("Tec-9 | Tornado (Field-Tested)", "Dust 2 Collection"),
                ("P2000 | Granite Marbleized (Field-Tested)", "Dust 2 Collection"),
            ]
        }

    def get_steam_market_price(self, item_name: str) -> Optional[float]:
        """Get current Steam market price for an item"""
        try:
            url = f"https://steamcommunity.com/market/priceoverview/"
            
            params = {
                'country': 'US',
                'currency': '1',  # USD
                'appid': '730',   # CS2
                'market_hash_name': item_name
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # Parse price string like "$1.23"
                    price_str = data.get('lowest_price', '').replace('$', '').replace(',', '')
                    if price_str:
                        return float(price_str)
            
            # Rate limiting
            time.sleep(1.1)  # Steam allows ~1 request per second
            
        except Exception as e:
            print(f"   ⚠️  Error fetching price for {item_name}: {e}")
        
        return None

    def estimate_price_if_unavailable(self, item_name: str, rarity: str) -> float:
        """Estimate price based on rarity and item type when Steam data unavailable"""
        base_prices = {
            "Consumer Grade": 0.10,
            "Industrial Grade": 0.25,
            "Mil-Spec Grade": 1.50,
            "Restricted": 8.00,
            "Classified": 25.00,
            "Covert": 100.00
        }
        
        base_price = base_prices.get(rarity, 1.0)
        
        # Adjust based on weapon popularity
        if any(weapon in item_name for weapon in ['AK-47', 'AWP', 'M4A4', 'M4A1-S']):
            base_price *= 2.0
        elif any(weapon in item_name for weapon in ['Glock-18', 'USP-S', 'P250']):
            base_price *= 1.2
        
        # Add variation to simulate market
        import random
        variation = random.uniform(0.7, 1.3)
        
        return round(base_price * variation, 2)

    def search_items_by_rarity(self, rarity: str, max_price: float = 10.0) -> List[MarketListing]:
        """Search for items of specific rarity within price range"""
        print(f"🔍 Searching for {rarity} items under ${max_price:.2f}...")
        
        items = self.sample_items.get(rarity, [])
        if not items:
            print(f"❌ No sample data for {rarity}")
            return []
        
        listings = []
        
        for item_name, collection in items:
            print(f"   📊 Checking: {item_name}")
            
            # Try to get real Steam price
            price = self.get_steam_market_price(item_name)
            
            if price is None:
                # Use estimated price if Steam API fails
                price = self.estimate_price_if_unavailable(item_name, rarity)
                print(f"      💭 Estimated: ${price:.2f}")
            else:
                print(f"      💰 Steam Market: ${price:.2f}")
            
            if price <= max_price:
                # Extract wear and calculate float
                wear = "Field-Tested"
                if "(Factory New)" in item_name:
                    wear = "Factory New"
                elif "(Minimal Wear)" in item_name:
                    wear = "Minimal Wear"
                elif "(Well-Worn)" in item_name:
                    wear = "Well-Worn"
                elif "(Battle-Scarred)" in item_name:
                    wear = "Battle-Scarred"
                
                float_ranges = {
                    "Factory New": 0.05,
                    "Minimal Wear": 0.12,
                    "Field-Tested": 0.25,
                    "Well-Worn": 0.45,
                    "Battle-Scarred": 0.75
                }
                
                listing = MarketListing(
                    item_name=item_name,
                    market_name="Steam Market",
                    price_usd=price,
                    float_value=float_ranges.get(wear, 0.25),
                    market_url=f"https://steamcommunity.com/market/listings/730/{urllib.parse.quote(item_name)}",
                    rarity=rarity,
                    collection=collection,
                    wear=wear
                )
                listings.append(listing)
        
        print(f"✅ Found {len(listings)} affordable items")
        return listings

    def calculate_output_value(self, output_rarity: str, input_float_avg: float) -> float:
        """Estimate output value based on rarity and expected float"""
        base_values = {
            "Industrial Grade": 1.20,
            "Mil-Spec Grade": 4.50,
            "Restricted": 15.00,
            "Classified": 45.00,
            "Covert": 200.00
        }
        
        base_value = base_values.get(output_rarity, 2.0)
        
        # Adjust for float (lower float = higher value)
        float_multiplier = 1.0 + (0.5 - input_float_avg) * 0.3
        float_multiplier = max(0.8, min(1.4, float_multiplier))
        
        return base_value * float_multiplier

    def find_profitable_combinations(self, listings: List[MarketListing], 
                                   min_profit: float = 1.0, 
                                   max_budget: float = 20.0) -> List[TradeUpOpportunity]:
        """Find profitable 10-item trade-up combinations"""
        print(f"\n🧮 Analyzing trade-up combinations...")
        print(f"Min profit: ${min_profit:.2f}, Max budget: ${max_budget:.2f}")
        
        opportunities = []
        
        # Group by collection for valid trade-ups
        by_collection = defaultdict(list)
        for listing in listings:
            if listing.price_usd <= max_budget / 10:
                by_collection[listing.collection].append(listing)
        
        for collection, items in by_collection.items():
            if len(items) < 10:
                print(f"   ⚠️  {collection}: Only {len(items)} items (need 10)")
                continue
                
            print(f"   🔍 Analyzing {collection} ({len(items)} items)")
            
            # Sort by price (cheapest first)
            items.sort(key=lambda x: x.price_usd)
            
            # Try different combinations
            for start_idx in range(min(5, len(items) - 10)):
                combination = items[start_idx:start_idx + 10]
                
                total_cost = sum(item.price_usd for item in combination)
                if total_cost > max_budget:
                    continue
                
                # Calculate average float
                avg_float = sum(item.float_value for item in combination) / len(combination)
                
                # Determine output rarity
                input_rarity = combination[0].rarity
                output_rarity = self.rarity_progression.get(input_rarity)
                if not output_rarity:
                    continue
                
                # Estimate output value
                estimated_output_value = self.calculate_output_value(output_rarity, avg_float)
                
                # Account for market fees
                net_output_value = estimated_output_value * (1 - self.steam_fee_rate)
                
                # Calculate profit
                profit = net_output_value - total_cost
                profit_percentage = (profit / total_cost) * 100 if total_cost > 0 else 0
                
                if profit >= min_profit:
                    opportunity = TradeUpOpportunity(
                        input_items=combination,
                        total_cost=total_cost,
                        expected_output_value=estimated_output_value,
                        estimated_profit=profit,
                        profit_percentage=profit_percentage,
                        output_rarity=output_rarity
                    )
                    opportunities.append(opportunity)
                    print(f"      ✅ Found opportunity: ${profit:.2f} profit ({profit_percentage:.1f}%)")
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        return opportunities

    def display_opportunity(self, opportunity: TradeUpOpportunity, index: int):
        """Display a trade-up opportunity in a readable format"""
        print(f"\n{'='*80}")
        print(f"💰 TRADE-UP OPPORTUNITY #{index + 1}")
        print(f"{'='*80}")
        print(f"Input → Output: {opportunity.input_items[0].rarity} → {opportunity.output_rarity}")
        print(f"Collection: {opportunity.input_items[0].collection}")
        print(f"Total Cost: ${opportunity.total_cost:.2f}")
        print(f"Expected Output Value: ${opportunity.expected_output_value:.2f} (before fees)")
        print(f"Net Profit: ${opportunity.estimated_profit:.2f} (after 15% Steam fee)")
        print(f"Profit Margin: {opportunity.profit_percentage:.1f}%")
        
        print(f"\n📋 ITEMS TO PURCHASE:")
        print(f"{'#':<3} {'Item Name':<45} {'Price':<8} {'Wear':<15} {'Float'}")
        print("-" * 80)
        
        for i, item in enumerate(opportunity.input_items, 1):
            print(f"{i:<3} {item.item_name[:44]:<45} ${item.price_usd:<7.2f} {item.wear:<15} {item.float_value:.3f}")
        
        print(f"\n🛒 PURCHASE INSTRUCTIONS:")
        print(f"   1. Go to Steam Community Market")
        print(f"   2. Search for each item above")
        print(f"   3. Buy the cheapest available listings")
        print(f"   4. Use CS2 Trade Up Contract with all 10 items")
        print(f"   5. Sell the output item on Steam Market")
        
        print(f"\n🔗 Quick Links:")
        print(f"   Steam Market: https://steamcommunity.com/market/search?appid=730")

    def run_analysis(self, 
                    rarity: str = "Mil-Spec Grade",
                    max_price_per_item: float = 3.0, 
                    min_profit: float = 1.0, 
                    max_budget: float = 20.0, 
                    max_opportunities: int = 3):
        """Run complete trade-up analysis"""
        print(f"\n🎯 CS2 Steam Market Trade-Up Finder")
        print(f"{'='*60}")
        print(f"Input Rarity: {rarity}")
        print(f"Max Price per Item: ${max_price_per_item:.2f}")
        print(f"Min Profit Required: ${min_profit:.2f}")
        print(f"Max Total Budget: ${max_budget:.2f}")
        print(f"Max Results: {max_opportunities}")
        
        # Search for items
        listings = self.search_items_by_rarity(rarity, max_price_per_item)
        
        if not listings:
            print("❌ No suitable items found")
            return
        
        # Find profitable combinations
        opportunities = self.find_profitable_combinations(listings, min_profit, max_budget)
        
        if not opportunities:
            print("\n❌ No profitable opportunities found")
            print("💡 Try:")
            print("   - Increasing max_price_per_item")
            print("   - Decreasing min_profit")
            print("   - Increasing max_budget")
            return
        
        print(f"\n🎯 TOP OPPORTUNITIES:")
        
        # Display top opportunities
        for i, opportunity in enumerate(opportunities[:max_opportunities]):
            self.display_opportunity(opportunity, i)
        
        if len(opportunities) > max_opportunities:
            print(f"\n... and {len(opportunities) - max_opportunities} more opportunities available")
        
        print(f"\n{'='*80}")
        print("🏁 Analysis Complete!")
        print("\n🔮 NEXT STEPS:")
        print("   • This demo uses Steam Market + sample data")
        print("   • For live multi-market data, upgrade to PriceEmpire paid API")
        print("   • Always verify current prices before purchasing")

def main():
    """Main CLI interface"""
    print("🎮 CS2 Trade-Up Finder - Steam Market Demo")
    print("=" * 50)
    print("This version uses free Steam Market API + sample data")
    print("Upgrade to PriceEmpire paid API for full multi-market support")
    
    # Initialize finder
    finder = SteamMarketTradeUpFinder()
    
    # Configuration
    print("\n⚙️  Configuration:")
    rarity = "Mil-Spec Grade"
    max_price_per_item = 3.00
    min_profit = 1.00
    max_budget = 25.00
    max_results = 2
    
    print(f"  Input rarity: {rarity}")
    print(f"  Max price per item: ${max_price_per_item:.2f}")
    print(f"  Min profit required: ${min_profit:.2f}")
    print(f"  Max total budget: ${max_budget:.2f}")
    print(f"  Max results to show: {max_results}")
    
    # Run analysis
    try:
        finder.run_analysis(rarity, max_price_per_item, min_profit, max_budget, max_results)
    except KeyboardInterrupt:
        print("\n👋 Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()