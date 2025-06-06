#!/usr/bin/env python3
"""
Multi-Market Trade-Up Finder for CS2 - Updated Version
Uses PriceEmpire API v4 to find profitable trade-ups across multiple markets
"""

import json
import requests
import time
import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class MarketListing:
    """Represents a skin listing on a specific market"""
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

class MultiMarketTradeUpFinder:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pricempire.com/v4/paid"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
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
        
        # Available markets/sources from PriceEmpire
        self.available_sources = [
            'steam', 'buff163', 'dmarket', 'lootfarm', 'skinport',
            'csmoney', 'swapgg', 'skinbaron', 'bitskins', 'tradeit',
            'skinbay', 'c5game', 'youpin898', 'waxpeer', 'lis_skins',
            'cs_deals', 'gamerpay', 'shadowpay', 'market_csgo', 'empire'
        ]
    
    def test_api_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            print("🔗 Testing PriceEmpire API connection...")
            
            # Test with a simple request to get item prices
            response = requests.get(
                f"{self.base_url}/items/prices",
                headers=self.headers,
                params={
                    'app_id': 730,  # CS2
                    'currency': 'USD'
                },
                timeout=15
            )
            
            if response.status_code == 200:
                print("✅ API connection successful!")
                return True
            elif response.status_code == 401:
                print("❌ Authentication failed - check your API key")
                return False
            else:
                print(f"❌ API Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def get_item_prices(self, sources: List[str] = None, limit: int = 100) -> List[MarketListing]:
        """Get item prices from multiple markets using PriceEmpire API"""
        if sources is None:
            sources = self.available_sources[:5]  # Use first 5 markets for testing
        
        try:
            print(f"📊 Fetching prices from markets: {', '.join(sources)}")
            
            response = requests.get(
                f"{self.base_url}/items/prices",
                headers=self.headers,
                params={
                    'app_id': 730,  # CS2
                    'sources': ','.join(sources),
                    'currency': 'USD'
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ API Error: HTTP {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return []
            
            data = response.json()
            listings = []
            
            print(f"📦 Processing {len(data)} items from API...")
            
            for item_data in data[:limit]:  # Limit results
                market_hash_name = item_data.get('market_hash_name', 'Unknown')
                prices = item_data.get('prices', [])
                
                # Extract basic item info (simplified for now)
                # In a real implementation, you'd parse the item name to extract rarity, collection, etc.
                item_rarity = self.extract_rarity_from_name(market_hash_name)
                if not item_rarity:
                    continue
                
                # Process each market price for this item
                for price_data in prices:
                    if price_data.get('price') is None:
                        continue
                        
                    price_usd = price_data.get('price', 0)
                    provider_key = price_data.get('provider_key', 'unknown')
                    
                    # Skip extremely expensive items for trade-ups
                    if price_usd > 50:
                        continue
                    
                    listing = MarketListing(
                        item_name=market_hash_name,
                        market_name=provider_key,
                        price_usd=price_usd,
                        float_value=0.25,  # Default float - would need separate API call for exact float
                        market_url=f"https://pricempire.com/item/{market_hash_name}",
                        rarity=item_rarity,
                        collection=self.extract_collection_from_name(market_hash_name),
                        wear=self.extract_wear_from_name(market_hash_name)
                    )
                    listings.append(listing)
            
            print(f"✅ Collected {len(listings)} listings from {len(sources)} markets")
            return listings
            
        except Exception as e:
            print(f"❌ Error fetching item prices: {e}")
            return []
    
    def extract_rarity_from_name(self, item_name: str) -> str:
        """Extract rarity from item name (simplified)"""
        # This is a simplified extraction - in reality you'd need a proper database
        # For now, we'll use some heuristics based on common patterns
        
        if "Consumer Grade" in item_name:
            return "Consumer Grade"
        elif "Industrial Grade" in item_name:
            return "Industrial Grade"
        elif "Mil-Spec" in item_name:
            return "Mil-Spec Grade"
        elif "Restricted" in item_name:
            return "Restricted"
        elif "Classified" in item_name:
            return "Classified"
        elif "Covert" in item_name:
            return "Covert"
        
        # Default assumptions based on weapon type (very rough)
        if any(weapon in item_name for weapon in ['AK-47', 'AWP', 'M4A4', 'M4A1-S']):
            return "Mil-Spec Grade"  # Common trade-up input
        elif any(weapon in item_name for weapon in ['Glock-18', 'USP-S', 'P250']):
            return "Industrial Grade"
        else:
            return "Mil-Spec Grade"  # Default for testing
    
    def extract_collection_from_name(self, item_name: str) -> str:
        """Extract collection from item name (simplified)"""
        # Simplified - would need proper database mapping
        if "Mirage" in item_name:
            return "Mirage Collection"
        elif "Dust" in item_name:
            return "Dust Collection"
        elif "Cache" in item_name:
            return "Cache Collection"
        else:
            return "Unknown Collection"
    
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
            return "Unknown"
    
    def calculate_output_value(self, output_rarity: str, input_float_avg: float) -> float:
        """Estimate output value based on rarity and expected float"""
        # Simplified conservative estimates in USD
        base_values = {
            "Industrial Grade": 0.80,
            "Mil-Spec Grade": 3.50,
            "Restricted": 12.00,
            "Classified": 35.00,
            "Covert": 150.00
        }
        
        base_value = base_values.get(output_rarity, 2.0)
        
        # Adjust for float (lower float = higher value)
        float_multiplier = 1.0 + (0.5 - input_float_avg) * 0.2
        float_multiplier = max(0.8, min(1.3, float_multiplier))
        
        return base_value * float_multiplier
    
    def find_profitable_combinations(self, listings: List[MarketListing], 
                                   min_profit: float = 1.0, 
                                   max_budget: float = 20.0,
                                   max_price_per_item: float = 3.0) -> List[TradeUpOpportunity]:
        """Find profitable 10-item trade-up combinations"""
        print(f"\\n🔍 Analyzing combinations...")
        print(f"Min profit: ${min_profit:.2f}, Max budget: ${max_budget:.2f}, Max per item: ${max_price_per_item:.2f}")
        
        opportunities = []
        
        # Filter items by price
        affordable_items = [item for item in listings if item.price_usd <= max_price_per_item]
        print(f"📋 {len(affordable_items)} items under ${max_price_per_item:.2f}")
        
        # Group by rarity for valid trade-ups
        by_rarity = defaultdict(list)
        for item in affordable_items:
            by_rarity[item.rarity].append(item)
        
        for input_rarity, items in by_rarity.items():
            output_rarity = self.rarity_progression.get(input_rarity)
            if not output_rarity or len(items) < 10:
                continue
                
            print(f"\\n📊 Analyzing {input_rarity} → {output_rarity} ({len(items)} items)")
            
            # Sort by price (cheapest first)
            items.sort(key=lambda x: x.price_usd)
            
            # Try combinations of 10 cheapest items
            for start_idx in range(min(10, len(items) - 10)):
                combination = items[start_idx:start_idx + 10]
                
                total_cost = sum(item.price_usd for item in combination)
                if total_cost > max_budget:
                    continue
                
                # Calculate average float
                avg_float = sum(item.float_value for item in combination) / len(combination)
                
                # Estimate output value
                estimated_output_value = self.calculate_output_value(output_rarity, avg_float)
                
                # Account for market fees (assume selling on Steam)
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
        
        # Sort by profit percentage
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        print(f"\\n✅ Found {len(opportunities)} profitable opportunities")
        return opportunities
    
    def display_opportunity(self, opportunity: TradeUpOpportunity, index: int):
        """Display a trade-up opportunity in a readable format"""
        print(f"\\n{'='*80}")
        print(f"💰 TRADE-UP OPPORTUNITY #{index + 1}")
        print(f"{'='*80}")
        print(f"Input → Output: {opportunity.input_items[0].rarity} → {opportunity.output_rarity}")
        print(f"Total Cost: ${opportunity.total_cost:.2f}")
        print(f"Expected Output Value: ${opportunity.expected_output_value:.2f} (before fees)")
        print(f"Net Profit: ${opportunity.estimated_profit:.2f} (after 15% Steam fee)")
        print(f"Profit Margin: {opportunity.profit_percentage:.1f}%")
        
        print(f"\\n📋 ITEMS TO PURCHASE:")
        print(f"{'#':<3} {'Item Name':<35} {'Market':<15} {'Price':<8} {'Wear'}")
        print("-" * 80)
        
        for i, item in enumerate(opportunity.input_items, 1):
            print(f"{i:<3} {item.item_name[:34]:<35} {item.market_name:<15} ${item.price_usd:<7.2f} {item.wear}")
        
        print(f"\\n🛒 MARKET BREAKDOWN:")
        market_counts = defaultdict(int)
        market_totals = defaultdict(float)
        
        for item in opportunity.input_items:
            market_counts[item.market_name] += 1
            market_totals[item.market_name] += item.price_usd
        
        for market, count in market_counts.items():
            total = market_totals[market]
            print(f"   {market}: {count} items, ${total:.2f}")
        
        print(f"\\n💡 Instructions:")
        print(f"   1. Buy all 10 items listed above")
        print(f"   2. Trade-up via CS2 in-game contract")
        print(f"   3. Sell output item on Steam Market")
        print(f"   4. Expected profit: ${opportunity.estimated_profit:.2f}")
    
    def run_analysis(self, 
                    max_price_per_item: float = 3.0, 
                    min_profit: float = 0.5, 
                    max_budget: float = 20.0, 
                    max_opportunities: int = 3):
        """Run complete trade-up analysis"""
        print(f"\\n🔍 CS2 Multi-Market Trade-Up Finder")
        print(f"{'='*60}")
        print(f"Max Price per Item: ${max_price_per_item:.2f}")
        print(f"Min Profit Required: ${min_profit:.2f}")
        print(f"Max Total Budget: ${max_budget:.2f}")
        print(f"Max Results: {max_opportunities}")
        
        # Test API connection
        if not self.test_api_connection():
            print("❌ Could not connect to PriceEmpire API")
            return
        
        # Get item prices from multiple markets
        print(f"\\n📈 Fetching live prices from multiple markets...")
        listings = self.get_item_prices(limit=200)  # Get more items for better opportunities
        
        if not listings:
            print("❌ No items found")
            return
        
        # Find profitable combinations
        opportunities = self.find_profitable_combinations(
            listings, min_profit, max_budget, max_price_per_item
        )
        
        if not opportunities:
            print("❌ No profitable opportunities found with current criteria")
            print("💡 Try:")
            print("   - Increasing max_price_per_item")
            print("   - Decreasing min_profit")
            print("   - Increasing max_budget")
            return
        
        print(f"\\n🎯 TOP OPPORTUNITIES:")
        
        # Display top opportunities
        for i, opportunity in enumerate(opportunities[:max_opportunities]):
            self.display_opportunity(opportunity, i)
        
        if len(opportunities) > max_opportunities:
            print(f"\\n... and {len(opportunities) - max_opportunities} more opportunities available")
        
        print(f"\\n{'='*80}")
        print("💰 Analysis Complete!")
        print("⚠️  IMPORTANT DISCLAIMERS:")
        print("   • Profits are estimates based on current market data")
        print("   • CS2 trade-up outcomes have random float values")
        print("   • Market prices change frequently")
        print("   • Always verify prices before purchasing")
        print("   • Consider market volatility and timing")
        print("🔄 Re-run analysis for latest market data")

def load_api_key():
    """Load API key from secrets.json"""
    try:
        with open("config/secrets.json", "r") as f:
            secrets = json.load(f)
            return secrets["api"]["priceempire_key"]
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None

def main():
    """Main CLI interface"""
    print("🎯 CS2 Multi-Market Trade-Up Finder v2")
    print("Finding profitable trade-ups using PriceEmpire API v4...")
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("❌ Could not load PriceEmpire API key from config/secrets.json")
        return
    
    print(f"✅ API key loaded: {api_key[:12]}...")
    
    # Initialize finder
    finder = MultiMarketTradeUpFinder(api_key)
    
    # Configuration for testing
    print("\\n⚙️  Using optimized configuration:")
    max_price_per_item = 3.00
    min_profit = 0.50
    max_budget = 20.00
    max_results = 3
    
    print(f"  Max price per item: ${max_price_per_item:.2f}")
    print(f"  Min profit required: ${min_profit:.2f}")
    print(f"  Max total budget: ${max_budget:.2f}")
    print(f"  Max results to show: {max_results}")
    
    # Run analysis
    try:
        finder.run_analysis(max_price_per_item, min_profit, max_budget, max_results)
    except KeyboardInterrupt:
        print("\\n👋 Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
