#!/usr/bin/env python3
"""
Multi-Market Trade-Up Finder for CS2
Uses PriceEmpire API to find profitable trade-ups across all 47 supported markets
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
        
    def get_all_markets(self) -> List[Dict]:
        """Get list of all supported markets"""
        try:
            print("🔗 Connecting to PriceEmpire API...")
            response = requests.get(f"{self.base_url}/markets", headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                markets = response.json()
                print(f"✅ Found {len(markets)} supported markets")
                return markets
            elif response.status_code == 401:
                print("❌ Authentication failed - check your API key")
                return []
            else:
                print(f"❌ API Error {response.status_code}: {response.text[:100]}")
                return []
        except requests.exceptions.Timeout:
            print("❌ Request timed out - check your internet connection")
            return []
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def search_items_across_markets(self, rarity: str, max_price: float = 50.0, limit: int = 100) -> List[MarketListing]:
        """Search for items of specific rarity across all markets"""
        print(f"Searching for {rarity} items under ${max_price:.2f} across all markets...")
        
        all_listings = []
        
        # Search parameters for PriceEmpire API
        params = {
            "game": "csgo",  # CS2 uses csgo game ID
            "rarity": rarity.lower().replace(" ", "_"),
            "max_price": int(max_price * 100),  # API expects cents
            "limit": limit,
            "sort": "price_asc"  # Cheapest first
        }
        
        try:
            response = requests.get(f"{self.base_url}/items/search", 
                                  headers=self.headers, 
                                  params=params, 
                                  timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                
                for item in items:
                    # Get market listings for this item
                    listings = self.get_item_listings(item["id"])
                    all_listings.extend(listings)
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
            else:
                print(f"Search failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error searching items: {e}")
        
        print(f"Found {len(all_listings)} listings for {rarity}")
        return all_listings
    
    def get_item_listings(self, item_id: str) -> List[MarketListing]:
        """Get all market listings for a specific item"""
        try:
            response = requests.get(f"{self.base_url}/items/{item_id}/listings", 
                                  headers=self.headers, 
                                  timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                listings = []
                
                for listing in data.get("listings", []):
                    market_listing = MarketListing(
                        item_name=listing.get("item_name", "Unknown"),
                        market_name=listing.get("market_name", "Unknown"),
                        price_usd=listing.get("price_usd", 0) / 100,  # Convert from cents
                        float_value=listing.get("float_value", 0.5),
                        market_url=listing.get("url", ""),
                        rarity=listing.get("rarity", "Unknown"),
                        collection=listing.get("collection", "Unknown"),
                        wear=listing.get("wear", "Unknown")
                    )
                    listings.append(market_listing)
                
                return listings
                
        except Exception as e:
            print(f"Error fetching listings for item {item_id}: {e}")
        
        return []
    
    def calculate_output_value(self, output_rarity: str, input_float_avg: float) -> float:
        """Estimate output value based on rarity and expected float"""
        # This is a simplified estimation - in reality you'd want to fetch actual output item prices
        base_values = {
            "Industrial Grade": 0.50,
            "Mil-Spec Grade": 2.00,
            "Restricted": 8.00,
            "Classified": 25.00,
            "Covert": 100.00
        }
        
        base_value = base_values.get(output_rarity, 1.0)
        
        # Adjust for float (lower float = higher value)
        float_multiplier = 1.0 + (0.5 - input_float_avg) * 0.3
        float_multiplier = max(0.7, min(1.5, float_multiplier))
        
        return base_value * float_multiplier
    
    def find_profitable_combinations(self, listings: List[MarketListing], 
                                   min_profit: float = 1.0, 
                                   max_budget: float = 20.0) -> List[TradeUpOpportunity]:
        """Find profitable 10-item trade-up combinations"""
        print(f"\\nAnalyzing combinations with min profit ${min_profit:.2f} and max budget ${max_budget:.2f}...")
        
        opportunities = []
        
        # Group by collection for valid trade-ups
        by_collection = defaultdict(list)
        for listing in listings:
            if listing.price_usd <= max_budget / 10:  # Each item can't be more than 1/10 of budget
                by_collection[listing.collection].append(listing)
        
        for collection, items in by_collection.items():
            if len(items) < 10:
                continue
                
            print(f"Analyzing {collection} collection ({len(items)} items)...")
            
            # Sort by price (cheapest first)
            items.sort(key=lambda x: x.price_usd)
            
            # Try different combinations
            for start_idx in range(min(20, len(items) - 10)):  # Limit combinations to avoid too much processing
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
        return opportunities
    
    def display_opportunity(self, opportunity: TradeUpOpportunity, index: int):
        """Display a trade-up opportunity in a readable format"""
        print(f"\\n{'='*80}")
        print(f"OPPORTUNITY #{index + 1}")
        print(f"{'='*80}")
        print(f"Output Rarity: {opportunity.output_rarity}")
        print(f"Total Cost: ${opportunity.total_cost:.2f}")
        print(f"Expected Output Value: ${opportunity.expected_output_value:.2f}")
        print(f"Estimated Profit: ${opportunity.estimated_profit:.2f}")
        print(f"Profit Percentage: {opportunity.profit_percentage:.1f}%")
        print(f"\\nItems to Buy:")
        print(f"{'Item Name':<40} {'Market':<15} {'Price':<8} {'Float':<8} {'Wear'}")
        print("-" * 80)
        
        for item in opportunity.input_items:
            print(f"{item.item_name[:39]:<40} {item.market_name:<15} ${item.price_usd:<7.2f} {item.float_value:<8.3f} {item.wear}")
        
        print(f"\\nMarket Summary:")
        market_counts = defaultdict(int)
        market_totals = defaultdict(float)
        
        for item in opportunity.input_items:
            market_counts[item.market_name] += 1
            market_totals[item.market_name] += item.price_usd
        
        for market, count in market_counts.items():
            total = market_totals[market]
            print(f"  {market}: {count} items, ${total:.2f}")
    
    def run_analysis(self, rarity: str = "Mil-Spec Grade", 
                    max_price: float = 10.0, 
                    min_profit: float = 1.0, 
                    max_budget: float = 50.0, 
                    max_opportunities: int = 5):
        """Run complete trade-up analysis"""
        print(f"\\n🔍 CS2 Multi-Market Trade-Up Finder")
        print(f"{'='*60}")
        print(f"Target Rarity: {rarity}")
        print(f"Max Price per Item: ${max_price:.2f}")
        print(f"Min Profit Required: ${min_profit:.2f}")
        print(f"Max Total Budget: ${max_budget:.2f}")
        print(f"Max Results: {max_opportunities}")
        
        # Get all available markets
        markets = self.get_all_markets()
        if not markets:
            print("❌ Could not fetch market data")
            return
        
        print(f"\\n📈 Searching across {len(markets)} markets...")
        
        # Search for items
        listings = self.search_items_across_markets(rarity, max_price)
        if not listings:
            print("❌ No items found matching criteria")
            return
        
        # Find profitable combinations
        opportunities = self.find_profitable_combinations(listings, min_profit, max_budget)
        
        if not opportunities:
            print("❌ No profitable opportunities found")
            print("💡 Try increasing max_price, decreasing min_profit, or increasing max_budget")
            return
        
        print(f"\\n✅ Found {len(opportunities)} profitable opportunities!")
        
        # Display top opportunities
        for i, opportunity in enumerate(opportunities[:max_opportunities]):
            self.display_opportunity(opportunity, i)
        
        if len(opportunities) > max_opportunities:
            print(f"\\n... and {len(opportunities) - max_opportunities} more opportunities")
        
        print(f"\\n{'='*80}")
        print("💰 Analysis Complete!")
        print("⚠️  Note: Prices and profits are estimates. Always verify current prices before purchasing.")
        print("🔄 Market prices change frequently - re-run analysis for latest data.")

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
    print("🎯 CS2 Multi-Market Trade-Up Finder")
    print("Finding profitable trade-ups across all PriceEmpire markets...")
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("❌ Could not load PriceEmpire API key from config/secrets.json")
        return
    
    print(f"✅ API key loaded: {api_key[:10]}...")
    
    # Initialize finder
    finder = MultiMarketTradeUpFinder(api_key)
    
    # Simple default configuration for testing
    print("\n⚙️  Using default configuration:")
    rarity = "Mil-Spec Grade"
    max_price = 3.00
    min_profit = 0.50
    max_budget = 20.00
    max_results = 3
    
    print(f"  Input rarity: {rarity}")
    print(f"  Max price per item: ${max_price:.2f}")
    print(f"  Min profit required: ${min_profit:.2f}")
    print(f"  Max total budget: ${max_budget:.2f}")
    print(f"  Max results to show: {max_results}")
    
    # Run analysis
    try:
        finder.run_analysis(rarity, max_price, min_profit, max_budget, max_results)
    except KeyboardInterrupt:
        print("\n👋 Analysis interrupted by user")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
