#!/usr/bin/env python3
"""
Steam Market Trade-Up Calculator for CS2
Uses Steam Community Market API to find profitable trade-ups.
"""

import json
import requests
import time
import sys
import os
import urllib.parse
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class SteamMarketListing:
    """Represents a skin listing on the Steam Market"""
    item_name: str
    price_usd: float
    float_value: float  # Steam API doesn't provide this directly, will be estimated
    market_url: str
    rarity: str
    collection: str
    wear: str
    quantity: int

@dataclass
class TradeUpOpportunity:
    """Represents a profitable trade-up opportunity"""
    input_items: List[SteamMarketListing]
    total_cost: float
    expected_output_value: float
    estimated_profit: float
    profit_percentage: float
    output_rarity: str

class SteamTradeUpCalculator:
    def __init__(self):
        self.base_url = "https://steamcommunity.com/market/listings/730"
        self.price_overview_url = "https://steamcommunity.com/market/priceoverview/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        self.rarity_progression = {
            "Consumer Grade": "Industrial Grade",
            "Industrial Grade": "Mil-Spec Grade",
            "Mil-Spec Grade": "Restricted",
            "Restricted": "Classified",
            "Classified": "Covert"
        }
        self.steam_fee_rate = 0.15 # Standard Steam Market fee (5% Steam + 10% game specific)
        self.request_delay = 2 # seconds, to avoid rate limiting

    def get_item_price(self, market_hash_name: str) -> Optional[Dict]:
        """Get the current price of an item from the Steam Market."""
        try:
            params = {
                'country': 'US',
                'currency': 1, # USD
                'appid': 730,
                'market_hash_name': market_hash_name
            }
            # print(f"Fetching price for: {market_hash_name}")
            response = requests.get(self.price_overview_url, params=params, headers=self.headers, timeout=10)
            time.sleep(self.request_delay) # Rate limiting

            if response.status_code == 200:
                data = response.json()
                if data and data.get('success'):
                    return data
            elif response.status_code == 429:
                print(f"Rate limited by Steam API. Waiting longer...")
                time.sleep(self.request_delay * 5)
                return self.get_item_price(market_hash_name) # Retry
            else:
                # print(f"Error fetching {market_hash_name}: HTTP {response.status_code} - {response.text[:100]}")
                pass # Often fails for items not currently on market, or due to rate limits
        except requests.exceptions.Timeout:
            print(f"Timeout fetching price for {market_hash_name}")
        except Exception as e:
            print(f"Error in get_item_price for {market_hash_name}: {e}")
        return None

    def search_items_by_rarity(self, target_rarity: str, max_items_to_check: int = 50) -> List[SteamMarketListing]:
        """Search for items of a specific rarity. 
        This is tricky with Steam API as there's no direct rarity search.
        We'll use a predefined list of items or try to infer from names.
        For now, this will be a placeholder and needs a robust item database.
        """
        print(f"\n⚠️  Steam API does not directly support searching by rarity.")
        print(f"This function needs a predefined list of items for {target_rarity}.")
        print(f"Using a small sample of Mil-Spec items for demonstration.")
        
        sample_mil_spec_items = [
            "MP7 | Cirrus (Factory New)",
            "MP7 | Cirrus (Minimal Wear)",
            "MP7 | Cirrus (Field-Tested)",
            "SG 553 | Integrale (Factory New)",
            "SG 553 | Integrale (Minimal Wear)",
            "SG 553 | Integrale (Field-Tested)",
            "UMP-45 | Momentum (Factory New)",
            "UMP-45 | Momentum (Minimal Wear)",
            "UMP-45 | Momentum (Field-Tested)",
            "Five-SeveN | Capillary (Factory New)",
            "Five-SeveN | Capillary (Minimal Wear)",
            "Five-SeveN | Capillary (Field-Tested)",
            "P250 | Sand Dune (Factory New)", # Cheap filler
            "P250 | Sand Dune (Minimal Wear)",
            "P250 | Sand Dune (Field-Tested)",
            "Tec-9 | Isaac (Factory New)",
            "Tec-9 | Isaac (Minimal Wear)",
            "Tec-9 | Isaac (Field-Tested)",
        ]
        
        # This should be dynamic based on target_rarity
        items_to_fetch = []
        if target_rarity == "Mil-Spec Grade":
            items_to_fetch = sample_mil_spec_items
        elif target_rarity == "Industrial Grade":
             items_to_fetch = [
                "P250 | Forest Night (Field-Tested)",
                "Nova | Forest Leaves (Field-Tested)",
                "PP-Bizon | Forest Leaves (Field-Tested)",
                "Sawed-Off | Forest DDPAT (Field-Tested)",
             ]
        else:
            print(f"No sample items defined for {target_rarity}. Add items to search_items_by_rarity.")
            return []

        listings = []
        print(f"Fetching prices for {len(items_to_fetch)} sample {target_rarity} items...")
        for i, item_name in enumerate(items_to_fetch[:max_items_to_check]):
            print(f" ({i+1}/{len(items_to_fetch)}) Fetching: {item_name}", end='\r')
            price_data = self.get_item_price(item_name)
            if price_data:
                price_str = price_data.get('lowest_price') or price_data.get('median_price')
                if price_str:
                    try:
                        # Price can be like "$0.03 USD" or "0,03€"
                        # Basic cleaning, assumes USD or similar format if no symbol
                        cleaned_price_str = price_str.replace("USD", "").replace("$", "").replace(",", ".").strip()
                        price_usd = float(cleaned_price_str)
                        quantity = int(price_data.get('volume', '0').replace(",",""))
                        
                        listing = SteamMarketListing(
                            item_name=item_name,
                            price_usd=price_usd,
                            float_value=0.25,  # Placeholder - Steam API doesn't provide this
                            market_url=f"{self.base_url}/{urllib.parse.quote(item_name)}",
                            rarity=self.extract_rarity_from_name(item_name) or target_rarity,
                            collection=self.extract_collection_from_name(item_name),
                            wear=self.extract_wear_from_name(item_name),
                            quantity=quantity
                        )
                        if quantity > 0: # Only add if items are on market
                             listings.append(listing)
                    except ValueError as ve:
                        print(f"\nCould not parse price for {item_name}: {price_str} -> {ve}")
                    except Exception as e:
                        print(f"\nError processing item {item_name}: {e}")
            sys.stdout.flush() # Ensure print(end='\r') updates correctly
        print("\nDone fetching sample item prices.")
        return listings

    def extract_rarity_from_name(self, item_name: str) -> str:
        # Simplified, ideally use a CS2 item database
        if "Consumer Grade" in item_name or any(p in item_name for p in ["Safari Mesh", "Sand Dune", "Forest DDPAT"]):
            return "Consumer Grade"
        if "Industrial Grade" in item_name or any(p in item_name for p in ["Boreal Forest", "Forest Leaves", "Urban DDPAT"]):
            return "Industrial Grade"
        if "Mil-Spec" in item_name or any(p in item_name for p in ["Capillary", "Cirrus", "Integrale", "Isaac", "Momentum"]):
            return "Mil-Spec Grade"
        if "Restricted" in item_name:
            return "Restricted"
        if "Classified" in item_name:
            return "Classified"
        if "Covert" in item_name:
            return "Covert"
        return "Unknown Rarity"

    def extract_collection_from_name(self, item_name: str) -> str:
        # Highly simplified, needs a proper database
        # Example: "AK-47 | Redline (Field-Tested)" -> Redline is part of "The Winter Offensive Collection"
        if "Collection" in item_name: # e.g. "The 2021 Mirage Collection"
            return item_name.split("|")[0].strip() if "|" in item_name else "Mixed Collection"
        # Add more known collection keywords if necessary
        return "Unknown Collection"

    def extract_wear_from_name(self, item_name: str) -> str:
        if "(Factory New)" in item_name: return "Factory New"
        if "(Minimal Wear)" in item_name: return "Minimal Wear"
        if "(Field-Tested)" in item_name: return "Field-Tested"
        if "(Well-Worn)" in item_name: return "Well-Worn"
        if "(Battle-Scarred)" in item_name: return "Battle-Scarred"
        return "Unknown Wear"

    def calculate_output_value(self, output_rarity: str, input_float_avg: float) -> float:
        # Simplified conservative estimates in USD. 
        # Ideally, fetch prices for potential output items.
        base_values = {
            "Industrial Grade": 0.10,
            "Mil-Spec Grade": 0.50,
            "Restricted": 2.50,
            "Classified": 10.00,
            "Covert": 40.00
        }
        base_value = base_values.get(output_rarity, 0.05) # Default to low value
        float_multiplier = 1.0 + (0.5 - input_float_avg) * 0.1 # Less impact from float for this simple model
        return base_value * max(0.8, min(1.2, float_multiplier))

    def find_profitable_combinations(self, listings: List[SteamMarketListing],
                                   input_target_rarity: str, 
                                   min_profit: float = 0.10, 
                                   max_budget: float = 5.0,
                                   max_price_per_item: float = 0.50) -> List[TradeUpOpportunity]:
        print(f"\n🔍 Analyzing combinations for {input_target_rarity} inputs...")
        opportunities = []
        
        # Filter by target input rarity and price
        input_items = [item for item in listings 
                       if item.rarity == input_target_rarity and item.price_usd <= max_price_per_item]
        
        if len(input_items) < 10:
            print(f"Not enough {input_target_rarity} items ({len(input_items)}) under ${max_price_per_item:.2f} to attempt a trade-up.")
            return []

        print(f"📋 {len(input_items)} affordable {input_target_rarity} items found.")
        input_items.sort(key=lambda x: x.price_usd)

        output_rarity = self.rarity_progression.get(input_target_rarity)
        if not output_rarity:
            print(f"Cannot determine output rarity for {input_target_rarity}.")
            return []

        # Simple combination: take the 10 cheapest items
        # More complex logic could try various combinations (itertools.combinations)
        if len(input_items) >= 10:
            combination = input_items[:10]
            total_cost = sum(item.price_usd for item in combination)

            if total_cost <= max_budget:
                avg_float = sum(item.float_value for item in combination) / 10.0
                estimated_output_value = self.calculate_output_value(output_rarity, avg_float)
                net_output_value = estimated_output_value * (1 - self.steam_fee_rate)
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
        
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        print(f"✅ Found {len(opportunities)} potential profitable combinations for {input_target_rarity} inputs.")
        return opportunities

    def display_opportunity(self, opportunity: TradeUpOpportunity, index: int):
        print(f"\n{'='*80}")
        print(f"💰 STEAM TRADE-UP OPPORTUNITY #{index + 1}")
        print(f"{'='*80}")
        print(f"Input Rarity: {opportunity.input_items[0].rarity} → Output Rarity: {opportunity.output_rarity}")
        print(f"Total Cost: ${opportunity.total_cost:.2f}")
        print(f"Expected Output Value (Steam Price): ${opportunity.expected_output_value:.2f} (before fees)")
        print(f"Estimated Net Profit: ${opportunity.estimated_profit:.2f} (after 15% Steam fee)")
        print(f"Profit Margin: {opportunity.profit_percentage:.1f}%")
        
        print(f"\n📋 ITEMS TO PURCHASE (from Steam Market):")
        print(f"{'#':<3} {'Item Name':<50} {'Price':<8} {'Qty':<8} {'Wear'}")
        print("-" * 90)
        for i, item in enumerate(opportunity.input_items, 1):
            print(f"{i:<3} {item.item_name:<50} ${item.price_usd:<7.2f} {item.quantity:<8} {item.wear}")
        print(f"\n💡 Instructions: Buy 10 cheapest of {opportunity.input_items[0].rarity} from the same collection (not yet enforced). Trade up.")

    def run_analysis(self, 
                    input_target_rarity: str = "Mil-Spec Grade",
                    max_price_per_item: float = 1.00, 
                    min_profit: float = 0.20, 
                    max_budget: float = 10.00, 
                    max_opportunities: int = 1):
        print(f"\n🔍 CS2 Steam Market Trade-Up Calculator")
        print(f"{'='*60}")
        print(f"Target Input Rarity: {input_target_rarity}")
        print(f"Max Price per Input Item: ${max_price_per_item:.2f}")
        print(f"Min Profit Required: ${min_profit:.2f}")
        print(f"Max Total Budget for 10 Inputs: ${max_budget:.2f}")
        
        listings = self.search_items_by_rarity(input_target_rarity)
        if not listings:
            print("❌ No items found for analysis based on current sample list.")
            return

        opportunities = self.find_profitable_combinations(
            listings, input_target_rarity, min_profit, max_budget, max_price_per_item
        )

        if not opportunities:
            print("❌ No profitable Steam Market opportunities found with current criteria & sample items.")
            print("💡 Try adjusting parameters or expanding the item list in `search_items_by_rarity`.")
            return
        
        print(f"\n🎯 TOP STEAM OPPORTUNITIES:")
        for i, opportunity in enumerate(opportunities[:max_opportunities]):
            self.display_opportunity(opportunity, i)
        
        print(f"\n{'='*80}")
        print("💰 Steam Analysis Complete!")
        print("⚠️  IMPORTANT: This tool uses a VERY SMALL, HARDCODED list of items for demonstration.")
        print("   For real use, `search_items_by_rarity` needs a comprehensive item database for the target rarity.")
        print("   Float values are placeholders. Collection matching for trade-ups is NOT YET IMPLEMENTED.")

def main():
    print("🎯 CS2 Steam Market Trade-Up Calculator")
    calculator = SteamTradeUpCalculator()
    
    # Configuration for testing
    # For Mil-Spec inputs, aiming for Restricted outputs
    calculator.run_analysis(
        input_target_rarity="Mil-Spec Grade",
        max_price_per_item=0.75, # Max price for each of the 10 Mil-Spec skins
        min_profit=0.10,         # Minimum profit after Steam fees
        max_budget=7.50,         # Max total cost for 10 Mil-Spec skins
        max_opportunities=2
    )
    # Example for Industrial Grade inputs
    # calculator.run_analysis(
    #     input_target_rarity="Industrial Grade",
    #     max_price_per_item=0.20, 
    #     min_profit=0.05,       
    #     max_budget=2.00,         
    #     max_opportunities=1
    # )

if __name__ == "__main__":
    main()
