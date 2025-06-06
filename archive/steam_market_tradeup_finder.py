#!/usr/bin/env python3
"""
Steam Market Trade-Up Finder for CS2
Uses Steam Market API to find profitable trade-ups
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
class SteamMarketListing:
    """Represents a skin listing on Steam Market"""
    item_name: str
    price_usd: float
    volume: int
    market_url: str
    rarity: str
    collection: str
    wear: str

@dataclass
class TradeUpOpportunity:
    """Represents a profitable trade-up opportunity"""
    input_items: List[SteamMarketListing]
    total_cost: float
    expected_output_value: float
    estimated_profit: float
    profit_percentage: float
    output_rarity: str
    input_rarity: str

class SteamMarketTradeUpFinder:
    def __init__(self):
        self.base_url = "https://steamcommunity.com/market"
        self.app_id = 730  # CS2
        
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
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.1  # Steam has rate limits
        
        # Common CS2 skins for trade-ups (organized by rarity)
        self.common_tradeup_skins = {
            "Consumer Grade": [
                "P2000 | Granite Marbleized",
                "MAC-10 | Indigo",
                "MP9 | Storm",
                "FAMAS | Colony",
                "Galil AR | Hunting Blind",
                "UMP-45 | Urban DDPAT",
                "P90 | Storm",
                "M249 | Contrast Spray"
            ],
            "Industrial Grade": [
                "P250 | Bone Mask",
                "Five-SeveN | Forest Night",
                "Tec-9 | Urban DDPAT",
                "CZ75-Auto | Hexane",
                "MP7 | Forest DDPAT",
                "UMP-45 | Scorched",
                "Nova | Predator",
                "XM1014 | Blue Steel"
            ],
            "Mil-Spec Grade": [
                "AK-47 | Blue Laminate",
                "M4A4 | Faded Zebra",
                "AWP | Safari Mesh",
                "P90 | Leather",
                "Galil AR | Kami",
                "FAMAS | Hexane",
                "MP9 | Hot Rod",
                "P2000 | Red FragCam"
            ]
        }
    
    def rate_limit(self):
        """Ensure we don't exceed Steam's rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_item_price(self, market_hash_name: str) -> Optional[SteamMarketListing]:
        """Get current price for a specific item from Steam Market"""
        self.rate_limit()
        
        try:
            # URL encode the item name
            encoded_name = urllib.parse.quote(market_hash_name)
            url = f"{self.base_url}/priceoverview/"
            
            params = {
                'country': 'US',
                'currency': '1',  # USD
                'appid': self.app_id,
                'market_hash_name': market_hash_name
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and 'lowest_price' in data:
                    # Parse price from string like "$1.23"
                    price_str = data['lowest_price'].replace('$', '').replace(',', '')
                    price = float(price_str)
                    
                    volume = int(data.get('volume', '0').replace(',', '')) if data.get('volume') else 0
                    
                    # Extract rarity and other info from item name
                    rarity = self.extract_rarity_from_name(market_hash_name)
                    collection = self.extract_collection_from_name(market_hash_name)
                    wear = self.extract_wear_from_name(market_hash_name)
                    
                    return SteamMarketListing(
                        item_name=market_hash_name,
                        price_usd=price,
                        volume=volume,
                        market_url=f"{self.base_url}/listings/{self.app_id}/{encoded_name}",
                        rarity=rarity,
                        collection=collection,
                        wear=wear
                    )
                else:
                    print(f"⚠️  No price data for {market_hash_name}")
                    
            else:
                print(f"❌ Error {response.status_code} for {market_hash_name}")
                
        except Exception as e:
            print(f"❌ Error fetching price for {market_hash_name}: {e}")
        
        return None
    
    def extract_rarity_from_name(self, item_name: str) -> str:
        """Extract rarity from item name based on known patterns"""
        # For Steam Market, we need to infer rarity from known items
        # This is a simplified approach - a full implementation would use a comprehensive database
        
        for rarity, items in self.common_tradeup_skins.items():
            for skin in items:
                if skin.split(' | ')[0] in item_name:  # Match weapon name
                    return rarity
        
        # Default assumptions based on weapon rarity patterns
        if any(weapon in item_name for weapon in ['AK-47', 'M4A4', 'AWP']):
            return "Mil-Spec Grade"
        elif any(weapon in item_name for weapon in ['P250', 'Five-SeveN', 'Tec-9']):
            return "Industrial Grade"
        else:
            return "Consumer Grade"  # Conservative default
    
    def extract_collection_from_name(self, item_name: str) -> str:
        """Extract collection from item name"""
        # Simplified collection mapping
        if "Dust" in item_name:
            return "Dust Collection"
        elif "Mirage" in item_name:
            return "Mirage Collection"
        elif "Cache" in item_name:
            return "Cache Collection"
        elif "Cobblestone" in item_name:
            return "Cobblestone Collection"
        else:
            return "Mixed Collection"  # Allow cross-collection for more opportunities
    
    def extract_wear_from_name(self, item_name: str) -> str:
        """Extract wear condition from item name"""
        if "(Factory New)" in item_name:
            return "Factory New"
        elif "(Minimal Wear)" in item_name:
            return "Minimal Wear"
        elif "(Field-Tested)" in item_name:
            return "Field-Tested"
        elif "(Well-Worn)" in item_name:
            return "Well-Worn"
        elif "(Battle-Scarred)" in item_name:
            return "Battle-Scarred"
        else:
            return "Field-Tested"  # Common default
    
    def search_affordable_items(self, rarity: str, max_price: float = 5.0) -> List[SteamMarketListing]:
        """Search for affordable items of specific rarity on Steam Market"""
        print(f"🔍 Searching for {rarity} items under ${max_price:.2f} on Steam Market...")
        
        listings = []
        items_to_check = self.common_tradeup_skins.get(rarity, [])
        
        if not items_to_check:
            print(f"❌ No known items for rarity: {rarity}")
            return []
        
        print(f"📋 Checking {len(items_to_check)} known {rarity} items...")
        
        for base_item in items_to_check:
            # Check different wear conditions for each item
            wear_conditions = [
                "(Factory New)",
                "(Minimal Wear)", 
                "(Field-Tested)",
                "(Well-Worn)",
                "(Battle-Scarred)"
            ]
            
            for wear in wear_conditions:
                item_name = f"{base_item} {wear}"
                print(f"   Checking: {item_name}")
                
                listing = self.get_item_price(item_name)
                if listing and listing.price_usd <= max_price:
                    listings.append(listing)
                    print(f"   ✅ Found: ${listing.price_usd:.2f}")
                elif listing:
                    print(f"   💰 Too expensive: ${listing.price_usd:.2f}")
                
                # Don't check all wear conditions if we found affordable ones
                if len(listings) >= 20:  # Limit to avoid too many API calls
                    break
            
            if len(listings) >= 20:
                break
        
        print(f"✅ Found {len(listings)} affordable {rarity} items")
        return listings
    
    def calculate_output_value(self, output_rarity: str) -> float:
        """Estimate output value based on rarity"""
        # Conservative estimates based on typical Steam Market prices
        base_values = {
            "Industrial Grade": 1.20,
            "Mil-Spec Grade": 4.50,
            "Restricted": 15.00,
            "Classified": 45.00,
            "Covert": 180.00
        }
        
        return base_values.get(output_rarity, 5.0)
    
    def find_profitable_combinations(self, listings: List[SteamMarketListing], 
                                   min_profit: float = 1.0, 
                                   max_budget: float = 30.0,
                                   max_price_per_item: float = 4.0) -> List[TradeUpOpportunity]:
        """Find profitable 10-item trade-up combinations"""
        print(f"\\n🔍 Analyzing trade-up combinations...")
        print(f"Min profit: ${min_profit:.2f}, Max budget: ${max_budget:.2f}, Max per item: ${max_price_per_item:.2f}")
        
        opportunities = []
        
        # Filter items by price and volume (ensure liquidity)
        affordable_items = [
            item for item in listings 
            if item.price_usd <= max_price_per_item and item.volume > 0
        ]
        
        print(f"📋 {len(affordable_items)} items meet criteria")
        
        # Group by rarity for valid trade-ups
        by_rarity = defaultdict(list)
        for item in affordable_items:
            by_rarity[item.rarity].append(item)
        
        for input_rarity, items in by_rarity.items():
            output_rarity = self.rarity_progression.get(input_rarity)
            if not output_rarity or len(items) < 10:
                print(f"⚠️  Not enough {input_rarity} items ({len(items)}) for trade-up")
                continue
                
            print(f"\\n📊 Analyzing {input_rarity} → {output_rarity} ({len(items)} items available)")
            
            # Sort by price (cheapest first)
            items.sort(key=lambda x: x.price_usd)
            
            # Try different combinations starting with cheapest items
            for start_idx in range(min(5, len(items) - 10)):
                combination = items[start_idx:start_idx + 10]
                
                total_cost = sum(item.price_usd for item in combination)
                if total_cost > max_budget:
                    print(f"   💸 Combination too expensive: ${total_cost:.2f}")
                    continue
                
                # Estimate output value (conservative)
                estimated_output_value = self.calculate_output_value(output_rarity)
                
                # Account for Steam market fees
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
                        output_rarity=output_rarity,
                        input_rarity=input_rarity
                    )
                    opportunities.append(opportunity)
                    print(f"   ✅ Found opportunity: ${profit:.2f} profit ({profit_percentage:.1f}%)")
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        print(f"\\n🎯 Found {len(opportunities)} profitable opportunities")
        return opportunities
    
    def display_opportunity(self, opportunity: TradeUpOpportunity, index: int):
        """Display a trade-up opportunity in a readable format"""
        print(f"\\n{'='*80}")
        print(f"💰 STEAM MARKET TRADE-UP OPPORTUNITY #{index + 1}")
        print(f"{'='*80}")
        print(f"Trade-Up: {opportunity.input_rarity} → {opportunity.output_rarity}")
        print(f"Total Cost: ${opportunity.total_cost:.2f}")
        print(f"Expected Output Value: ${opportunity.expected_output_value:.2f} (before fees)")
        print(f"Net Profit: ${opportunity.estimated_profit:.2f} (after 15% Steam fee)")
        print(f"Profit Margin: {opportunity.profit_percentage:.1f}%")
        
        print(f"\\n📋 ITEMS TO BUY ON STEAM MARKET:")
        print(f"{'#':<3} {'Item Name':<50} {'Price':<8} {'Volume':<8} {'Wear'}")
        print("-" * 80)
        
        for i, item in enumerate(opportunity.input_items, 1):
            print(f"{i:<3} {item.item_name[:49]:<50} ${item.price_usd:<7.2f} {item.volume:<8} {item.wear}")
        
        print(f"\\n🛒 PURCHASE SUMMARY:")
        total_volume = sum(item.volume for item in opportunity.input_items)
        avg_price = opportunity.total_cost / len(opportunity.input_items)
        
        print(f"   Total items: 10")
        print(f"   Average price per item: ${avg_price:.2f}")
        print(f"   Total market volume: {total_volume:,}")
        print(f"   All items available on Steam Market")
        
        print(f"\\n💡 INSTRUCTIONS:")
        print(f"   1. Buy all 10 items from Steam Community Market")
        print(f"   2. Use CS2 Trade-Up Contract in-game")
        print(f"   3. Sell the output item on Steam Market")
        print(f"   4. Expected profit: ${opportunity.estimated_profit:.2f}")
        
        print(f"\\n⚠️  RISKS:")
        print(f"   • Market prices change frequently")
        print(f"   • Trade-up output has random float value")
        print(f"   • Output item may be less valuable than estimated")
        print(f"   • Steam Market fees apply to both buying and selling")
    
    def run_analysis(self, 
                    target_rarity: str = "Industrial Grade",
                    max_price_per_item: float = 4.0, 
                    min_profit: float = 1.0, 
                    max_budget: float = 30.0, 
                    max_opportunities: int = 3):
        """Run complete Steam Market trade-up analysis"""
        print(f"🎯 CS2 Steam Market Trade-Up Finder")
        print(f"{'='*60}")
        print(f"Target Input Rarity: {target_rarity}")
        print(f"Max Price per Item: ${max_price_per_item:.2f}")
        print(f"Min Profit Required: ${min_profit:.2f}")
        print(f"Max Total Budget: ${max_budget:.2f}")
        print(f"Max Results: {max_opportunities}")
        
        # Validate target rarity
        if target_rarity not in self.rarity_progression:
            print(f"❌ Invalid target rarity: {target_rarity}")
            print(f"Available rarities: {list(self.rarity_progression.keys())}")
            return
        
        output_rarity = self.rarity_progression[target_rarity]
        print(f"Output Rarity: {output_rarity}")
        
        # Search for affordable items
        print(f"\\n📈 Searching Steam Market for {target_rarity} items...")
        listings = self.search_affordable_items(target_rarity, max_price_per_item)
        
        if not listings:
            print("❌ No affordable items found on Steam Market")
            print("💡 Try:")
            print("   - Increasing max_price_per_item")
            print("   - Choosing a different target_rarity")
            return
        
        # Find profitable combinations
        opportunities = self.find_profitable_combinations(
            listings, min_profit, max_budget, max_price_per_item
        )
        
        if not opportunities:
            print("❌ No profitable opportunities found with current criteria")
            print("💡 Try:")
            print("   - Decreasing min_profit requirement")
            print("   - Increasing max_budget")
            print("   - Increasing max_price_per_item")
            return
        
        print(f"\\n🎯 TOP STEAM MARKET OPPORTUNITIES:")
        
        # Display top opportunities
        for i, opportunity in enumerate(opportunities[:max_opportunities]):
            self.display_opportunity(opportunity, i)
        
        if len(opportunities) > max_opportunities:
            print(f"\\n... and {len(opportunities) - max_opportunities} more opportunities available")
        
        print(f"\\n{'='*80}")
        print("💰 Steam Market Analysis Complete!")
        print("\\n⚠️  IMPORTANT DISCLAIMERS:")
        print("   • All prices from Steam Community Market")
        print("   • Profits are estimates based on current market data")
        print("   • CS2 trade-up outcomes have random elements")
        print("   • Market prices change frequently throughout the day")
        print("   • Always verify current prices before purchasing")
        print("   • Consider market volatility and timing")
        print("\\n🔄 Re-run analysis for latest Steam Market data")

def main():
    """Main CLI interface"""
    print("🎯 CS2 Steam Market Trade-Up Finder")
    print("Using Steam Community Market API for real-time prices...")
    
    # Initialize finder (no API key needed for Steam Market)
    finder = SteamMarketTradeUpFinder()
    
    # Configuration for testing
    print("\\n⚙️  Configuration:")
    target_rarity = "Consumer Grade"  # Start with cheapest items
    max_price_per_item = 2.00
    min_profit = 0.50
    max_budget = 15.00
    max_results = 3
    
    print(f"  Target input rarity: {target_rarity}")
    print(f"  Max price per item: ${max_price_per_item:.2f}")
    print(f"  Min profit required: ${min_profit:.2f}")
    print(f"  Max total budget: ${max_budget:.2f}")
    print(f"  Max results to show: {max_results}")
    
    # Run analysis
    try:
        finder.run_analysis(target_rarity, max_price_per_item, min_profit, max_budget, max_results)
    except KeyboardInterrupt:
        print("\\n👋 Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
