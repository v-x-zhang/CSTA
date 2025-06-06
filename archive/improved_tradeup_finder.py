#!/usr/bin/env python3
"""
Improved Multi-Market Trade-Up Finder for CS2
Uses PriceEmpire API v4 with proper filtering and validation
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
    item_type: str  # 'weapon', 'sticker', 'case', etc.

@dataclass
class TradeUpOpportunity:
    """Represents a profitable trade-up opportunity"""
    input_items: List[MarketListing]
    total_cost: float
    expected_output_value: float
    estimated_profit: float
    profit_percentage: float
    output_rarity: str
    collection: str

class ImprovedTradeUpFinder:
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
        
        self.steam_fee_rate = 0.15
        
        # Market sources to use (limit to most reliable ones)
        self.preferred_sources = ['steam', 'buff163', 'dmarket', 'skinport', 'csmoney']
    
    def test_api_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            print("🔗 Testing PriceEmpire API connection...")
            response = requests.get(
                f"{self.base_url}/items/prices",
                headers=self.headers,
                params={'app_id': 730, 'currency': 'USD'},
                timeout=15
            )
            
            if response.status_code == 200:
                print("✅ API connection successful!")
                return True
            else:
                print(f"❌ API Error: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def is_tradeable_weapon(self, item_name: str) -> bool:
        """Check if item is a tradeable weapon/knife skin (not sticker, case, etc.)"""
        # Exclude non-tradeable items
        exclude_keywords = [
            'Sticker |', 'Souvenir ', 'StatTrak™ Music Kit',
            'Music Kit |', 'Graffiti |', 'Patch |', 'Case',
            'Key', 'Pass', 'Pin', 'Collectible'
        ]
        
        if any(keyword in item_name for keyword in exclude_keywords):
            return False
        
        # Include weapon skins and knives
        weapon_keywords = [
            'AK-47 |', 'M4A4 |', 'M4A1-S |', 'AWP |', 'Glock-18 |',
            'USP-S |', 'P250 |', 'Tec-9 |', 'Five-SeveN |', 'CZ75-Auto |',
            'Desert Eagle |', 'Dual Berettas |', 'P2000 |', 'MAC-10 |',
            'MP9 |', 'MP7 |', 'UMP-45 |', 'P90 |', 'PP-Bizon |',
            'Nova |', 'XM1014 |', 'MAG-7 |', 'Sawed-Off |', 'M249 |',
            'Negev |', 'FAMAS |', 'Galil AR |', 'SG 553 |', 'AUG |',
            'SSG 08 |', 'SCAR-20 |', 'G3SG1 |', '★ ', 'Karambit |',
            'Bayonet |', 'Flip Knife |', 'Gut Knife |'        ]
        
        return any(keyword in item_name for keyword in weapon_keywords)
    
    def extract_collection_from_name(self, item_name: str) -> str:
        """Extract collection from item name using known CS2 collections"""
        # Major CS2 Collections with common skins
        collection_patterns = {
            # Popular Collections
            'The Dust 2 Collection': ['Desert Eagle | Blaze', 'P90 | Desert Warfare'],
            'The Italy Collection': ['Five-SeveN | Silver Quartz', 'Tec-9 | Tornado'],
            'The Lake Collection': ['Caiman', 'Hot Rod', 'Copper Galaxy'],
            'The Safehouse Collection': ['Contractor', 'Urban Perforated'],
            'The Train Collection': ['Eco', 'Dazzle'],
            'The Mirage Collection': ['Sonar', 'Amber Fade'],
            'The Cache Collection': ['Bullet Rain', 'Pulse'],
            'The Cobblestone Collection': ['Dragon Lore', 'Knight'],
            'The Overpass Collection': ['Pink DDPAT', 'Green Apple'],
            'The Blacksite Collection': ['Bloodsport', 'Mecha Industries'],
            
            # Operation Collections
            'The Bravo Collection': ['Fire Serpent', 'Golden Koi', 'Graphite'],
            'The Phoenix Collection': ['Asiimov', 'Redline', 'Red Laminate'],
            'The Huntsman Collection': ['Vulcan', 'Howl', 'Cyrex'],
            'The Breakout Collection': ['Butterfly', 'Retribution'],
            'The Vanguard Collection': ['Basilisk', 'Graven'],
            'The Chroma Collection': ['Hyper Beast', 'Damascus Steel'],
            'The Falchion Collection': ['Aquamarine Revenge', 'Elite Build'],
            'The Shadow Collection': ['Shadow Daggers', 'Duelist'],
            'The Revolver Collection': ['Fuel Rod', 'Amber Fade'],
            'The Wildfire Collection': ['Elite Build', 'Phobos'],
            'The Gamma Collection': ['Lore', 'Autotronic'],
            'The Glove Collection': ['Bloodhound', 'Driver'],
            'The Spectrum Collection': ['Chromatic Aberration', 'Goo'],
            'The Clutch Collection': ['See Ya Later', 'Mortis'],
            'The Horizon Collection': ['Neo-Noir', 'Daimyo'],
            'The Danger Zone Collection': ['Facility Dark', 'Jungle Slipstream'],
            'The Prisma Collection': ['The Empress', 'Nevermore'],
            'The CS20 Collection': ['Printstream', 'Ancient Earth'],
            'The Shattered Web Collection': ['Gungnir', 'Wild Lotus'],
            'The Control Collection': ['Printstream', 'Ancient Earth'],
            'The Havoc Collection': ['AK-47 | Inheritance', 'AWP | Containment Breach'],
            'The Revolution Collection': ['AK-47 | Inheritance', 'M4A4 | Temukau'],
        }
        
        # Check for specific skin patterns
        for collection, skins in collection_patterns.items():
            for skin in skins:
                if skin.lower() in item_name.lower():
                    return collection
        
        # Weapon-based fallback groupings for trade-up compatibility
        if any(weapon in item_name for weapon in ['AK-47 |', 'M4A4 |', 'M4A1-S |']):
            return 'Rifle Collection'
        elif 'AWP |' in item_name:
            return 'Sniper Collection'  
        elif any(weapon in item_name for weapon in ['Glock-18 |', 'USP-S |', 'P250 |', 'Desert Eagle |']):
            return 'Pistol Collection'
        elif any(weapon in item_name for weapon in ['MAC-10 |', 'MP9 |', 'UMP-45 |', 'P90 |']):
            return 'SMG Collection'
        elif any(weapon in item_name for weapon in ['Nova |', 'XM1014 |', 'MAG-7 |', 'Sawed-Off |']):
            return 'Shotgun Collection'
        elif '★' in item_name:
            return 'Knife Collection'
        
        return 'Unknown Collection'    
    
    def get_filtered_items(self, limit: int = 1000) -> List[MarketListing]:
        """Get filtered tradeable weapon skins with valid prices"""
        try:
            print(f"📊 Fetching weapon skins from PriceEmpire...")
            
            response = requests.get(
                f"{self.base_url}/items/prices",
                headers=self.headers,
                params={
                    'app_id': 730,
                    'sources': ','.join(self.preferred_sources),
                    'currency': 'USD',
                    'language': 'en'
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ API Error: HTTP {response.status_code}")
                return []
            
            data = response.json()
            # Cache the market data for output value calculations
            self._market_cache = data
            listings = []
            
            print(f"📦 Processing {len(data)} items from API...")
            processed = 0
            
            for item_data in data:
                if processed >= limit:
                    break
                    
                market_hash_name = item_data.get('market_hash_name', '')
                
                # Filter to only tradeable weapons
                if not self.is_tradeable_weapon(market_hash_name):
                    continue
                
                # Extract rarity for trade-up validation
                rarity = self.extract_rarity_from_name(market_hash_name)
                if rarity == "Unknown":
                    continue
                
                prices = item_data.get('prices', [])
                
                # Process each market price for this item
                for price_data in prices:
                    price_value = price_data.get('price')
                    if price_value is None or price_value <= 0:
                        continue
                        
                    provider_key = price_data.get('provider_key', 'unknown')
                    
                    # Skip extremely expensive items (over $10 for trade-ups)
                    if price_value > 10:
                        continue
                    
                    listing = MarketListing(
                        item_name=market_hash_name,
                        market_name=provider_key,
                        price_usd=price_value,
                        float_value=0.25,  # Default - would need separate API call
                        market_url=f"https://pricempire.com/item/{market_hash_name}",
                        rarity=rarity,
                        collection=self.extract_collection_from_name(market_hash_name),
                        wear=self.extract_wear_from_name(market_hash_name),
                        item_type='weapon'
                    )
                    listings.append(listing)
                
                processed += 1
                if processed % 100 == 0:
                    print(f"   Processed {processed} items, found {len(listings)} valid listings...")
            
            print(f"✅ Collected {len(listings)} weapon skin listings")
            return listings
            
        except Exception as e:
            print(f"❌ Error fetching items: {e}")
            return []
    
    def extract_rarity_from_name(self, item_name: str) -> str:
        """Extract rarity from item name using patterns"""
        # Use weapon type as rough rarity indicator
        if any(weapon in item_name for weapon in ['★', 'Karambit', 'Bayonet', 'Knife']):
            return "Covert"  # Knives are typically highest tier
        elif any(weapon in item_name for weapon in ['AK-47', 'M4A4', 'AWP']):
            return "Mil-Spec Grade"  # Common trade-up inputs
        elif any(weapon in item_name for weapon in ['Glock-18', 'USP-S', 'P250']):
            return "Industrial Grade"
        elif any(weapon in item_name for weapon in ['MP7', 'MP9', 'UMP-45']):
            return "Mil-Spec Grade"
        else:
            return "Mil-Spec Grade"  # Default for most weapons
    
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

    def get_potential_outputs_from_market(self, input_rarity: str, collection: str) -> List[str]:
        """Get real potential output items from current market data"""
        output_rarity = self.rarity_progression.get(input_rarity)
        if not output_rarity:
            return []
        
        try:
            # Use cached market data if available, otherwise fetch fresh
            if not hasattr(self, '_market_cache'):
                response = requests.get(
                    f"{self.base_url}/items/prices",
                    headers=self.headers,
                    params={
                        'app_id': 730,
                        'language': 'en',
                        'currency': 'USD'
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    self._market_cache = response.json()
                else:
                    return []
            
            potential_outputs = []
            rarity_counts = defaultdict(int)
            
            # Look for items of the target output rarity
            for item_data in self._market_cache:
                market_hash_name = item_data.get('market_hash_name', '')
                
                # Skip non-weapons
                if not self.is_tradeable_weapon(market_hash_name):
                    continue
                
                # Check if this item matches the output rarity
                item_rarity = self.extract_rarity_from_name(market_hash_name)
                rarity_counts[item_rarity] += 1
                
                if item_rarity != output_rarity:
                    continue
                
                # For weapon-based collections, look for same weapon type
                if 'Rifle' in collection and any(weapon in market_hash_name for weapon in ['AK-47 |', 'M4A4 |', 'M4A1-S |']):
                    potential_outputs.append(market_hash_name)
                elif 'Sniper' in collection and 'AWP |' in market_hash_name:
                    potential_outputs.append(market_hash_name)
                elif 'Pistol' in collection and any(weapon in market_hash_name for weapon in ['Glock-18 |', 'USP-S |', 'Desert Eagle |']):
                    potential_outputs.append(market_hash_name)
                elif 'SMG' in collection and any(weapon in market_hash_name for weapon in ['P90 |', 'MP9 |', 'MAC-10 |']):
                    potential_outputs.append(market_hash_name)
                elif collection not in ['Rifle Collection', 'Sniper Collection', 'Pistol Collection', 'SMG Collection']:
                    # For specific collections, be more lenient
                    potential_outputs.append(market_hash_name)
                  # Limit to reasonable number for analysis
                if len(potential_outputs) >= 20:
                    break
            
            print(f"   📊 Rarity breakdown: {dict(rarity_counts)}")
            print(f"   🎯 Looking for {output_rarity}, found {len(potential_outputs)} matches")
            return potential_outputs[:10]  # Return top 10 for analysis
            
        except Exception as e:
            print(f"❌ Error getting potential outputs: {e}")
            return []    
        
    def calculate_real_output_value(self, input_rarity: str, collection: str) -> float:
        """Calculate expected output value using real market prices"""
        potential_outputs = self.get_potential_outputs_from_market(input_rarity, collection)
        print(f"   🔍 Found {len(potential_outputs)} potential outputs for {input_rarity} → {self.rarity_progression.get(input_rarity)}")
        
        if not potential_outputs:
            # Fallback to conservative estimates if no real outputs found
            output_rarity = self.rarity_progression.get(input_rarity, "Mil-Spec Grade")
            fallback_values = {
                "Mil-Spec Grade": 0.50,
                "Restricted": 2.00,
                "Classified": 8.00,
                "Covert": 25.00
            }
            print(f"   ⚠️  No potential outputs found, using fallback: ${fallback_values.get(output_rarity, 1.0):.2f}")
            return fallback_values.get(output_rarity, 1.0)
        
        # Get real market prices for potential outputs
        total_value = 0
        valid_prices = 0
        
        for output_name in potential_outputs:
            # Find this item in our cached market data
            for item_data in getattr(self, '_market_cache', []):
                if item_data.get('market_hash_name') == output_name:
                    prices = item_data.get('prices', [])
                    # Get best price from preferred sources
                    item_prices = [p.get('price') for p in prices 
                                 if p.get('provider_key') in self.preferred_sources 
                                 and p.get('price') and p.get('price') > 0]
                    if item_prices:
                        total_value += min(item_prices)  # Use lowest price (most conservative)
                        valid_prices += 1
                    break
        
        if valid_prices == 0:
            # Fallback if no valid prices found
            output_rarity = self.rarity_progression.get(input_rarity, "Mil-Spec Grade")
            fallback_values = {
                "Mil-Spec Grade": 0.50,
                "Restricted": 2.00,
                "Classified": 8.00,
                "Covert": 25.00
            }
            return fallback_values.get(output_rarity, 1.0)
        
        # Calculate average value of potential outputs
        avg_price = total_value / valid_prices
        print(f"   📈 Real market data: {valid_prices}/{len(potential_outputs)} outputs priced, avg ${avg_price:.2f}")
        
        return avg_price
    
    def find_collection_opportunities(self, listings: List[MarketListing], 
                                    min_profit: float = 1.0, 
                                    max_budget: float = 15.0,
                                    max_price_per_item: float = 2.0) -> List[TradeUpOpportunity]:
        """Find profitable trade-up opportunities within same collections"""
        print(f"\\n🔍 Finding collection-based trade-up opportunities...")
        
        opportunities = []
        
        # Group by collection and rarity
        by_collection_rarity = defaultdict(list)
        for item in listings:
            if item.price_usd <= max_price_per_item and item.price_usd > 0:
                key = (item.collection, item.rarity)
                by_collection_rarity[key].append(item)
        
        print(f"📋 Found {len(by_collection_rarity)} collection-rarity combinations")
        for (collection, input_rarity), items in by_collection_rarity.items():
            output_rarity = self.rarity_progression.get(input_rarity)
            if not output_rarity:
                continue
                
            # Analyze even smaller groups to identify potential opportunities
            min_items_needed = 5 if len(items) >= 5 else len(items)
            if len(items) < 3:  # Skip if too few items
                continue
                
            print(f"\\n📊 Analyzing {collection} - {input_rarity} → {output_rarity} ({len(items)} items)")
            
            if len(items) >= 10:
                print(f"   ✅ Full trade-up possible with 10 items")
            else:
                print(f"   ⚠️  Need {10 - len(items)} more items for complete trade-up")
                
            # Sort by price (cheapest first)
            items.sort(key=lambda x: x.price_usd)
            
            # Take cheapest available items (up to 10)
            combination = items[:min(10, len(items))]
            
            # For incomplete sets, estimate mixed collection approach
            items_needed = 10 - len(combination)
            if items_needed > 0:
                # Find cheapest items from same rarity in other collections
                other_items = [item for other_key, other_items in by_collection_rarity.items() 
                             if other_key[1] == input_rarity and other_key[0] != collection 
                             for item in other_items]
                other_items.sort(key=lambda x: x.price_usd)
                combination.extend(other_items[:items_needed])
            if len(combination) < 10:
                print(f"   ❌ Only {len(combination)} total items available")
                continue
            
            total_cost = sum(item.price_usd for item in combination)
            
            if total_cost > max_budget:
                print(f"   Skipping - total cost ${total_cost:.2f} exceeds budget ${max_budget:.2f}")
                continue            # Calculate expected output value using real market data
            estimated_output_value = self.calculate_real_output_value(input_rarity, collection)
            net_output_value = estimated_output_value * (1 - self.steam_fee_rate)
            profit = net_output_value - total_cost
            profit_percentage = (profit / total_cost) * 100 if total_cost > 0 else 0
            
            print(f"   💰 Cost: ${total_cost:.2f} | Output: ${estimated_output_value:.2f} | After fees: ${net_output_value:.2f} | Profit: ${profit:.2f}")
            
            if profit >= min_profit:
                opportunity = TradeUpOpportunity(
                    input_items=combination,
                    total_cost=total_cost,
                    expected_output_value=estimated_output_value,
                    estimated_profit=profit,
                    profit_percentage=profit_percentage,
                    output_rarity=output_rarity,
                    collection=collection
                )
                opportunities.append(opportunity)
                print(f"   ✅ Found profitable opportunity: ${profit:.2f} profit ({profit_percentage:.1f}%)")
            else:
                print(f"   ❌ Not profitable: ${profit:.2f} profit (need ${min_profit:.2f})")
        
        opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        return opportunities
    
    def display_opportunity(self, opportunity: TradeUpOpportunity, index: int):
        """Display a trade-up opportunity"""
        print(f"\\n{'='*80}")
        print(f"💰 TRADE-UP OPPORTUNITY #{index + 1}")
        print(f"{'='*80}")
        print(f"Collection: {opportunity.collection}")
        print(f"Input → Output: {opportunity.input_items[0].rarity} → {opportunity.output_rarity}")
        print(f"Total Cost: ${opportunity.total_cost:.2f}")
        print(f"Expected Output Value: ${opportunity.expected_output_value:.2f} (before fees)")
        print(f"Net Profit: ${opportunity.estimated_profit:.2f} (after 15% Steam fee)")
        print(f"Profit Margin: {opportunity.profit_percentage:.1f}%")
        
        print(f"\\n📋 ITEMS TO PURCHASE:")
        print(f"{'#':<3} {'Item Name':<45} {'Market':<12} {'Price':<8} {'Wear'}")
        print("-" * 80)
        
        for i, item in enumerate(opportunity.input_items, 1):
            print(f"{i:<3} {item.item_name[:44]:<45} {item.market_name:<12} ${item.price_usd:<7.2f} {item.wear}")
        
        print(f"\\n🛒 MARKET BREAKDOWN:")
        market_summary = defaultdict(lambda: {'count': 0, 'total': 0.0})
        for item in opportunity.input_items:
            market_summary[item.market_name]['count'] += 1
            market_summary[item.market_name]['total'] += item.price_usd
        
        for market, data in market_summary.items():
            print(f"   {market}: {data['count']} items, ${data['total']:.2f}")
    
    def run_analysis(self, 
                    max_price_per_item: float = 2.0, 
                    min_profit: float = 1.0, 
                    max_budget: float = 15.0, 
                    max_opportunities: int = 3):
        """Run complete trade-up analysis"""
        print(f"\\n🎯 CS2 Collection-Based Trade-Up Finder")
        print(f"{'='*60}")
        print(f"Max Price per Item: ${max_price_per_item:.2f}")
        print(f"Min Profit Required: ${min_profit:.2f}")
        print(f"Max Total Budget: ${max_budget:.2f}")
        print(f"Max Results: {max_opportunities}")
        
        # Test API connection
        if not self.test_api_connection():
            return
          # Get filtered weapon skins
        listings = self.get_filtered_items(limit=5000)  # Process more items
        if not listings:
            print("❌ No weapon skins found")
            return
        
        # Find collection-based opportunities
        opportunities = self.find_collection_opportunities(
            listings, min_profit, max_budget, max_price_per_item
        )
        
        if not opportunities:
            print("❌ No profitable collection-based opportunities found")
            print("💡 Try adjusting parameters or wait for market changes")
            return
        
        print(f"\\n🎯 TOP COLLECTION-BASED OPPORTUNITIES:")
        
        # Display top opportunities
        for i, opportunity in enumerate(opportunities[:max_opportunities]):
            self.display_opportunity(opportunity, i)
        
        if len(opportunities) > max_opportunities:
            print(f"\\n... and {len(opportunities) - max_opportunities} more opportunities")
        
        print(f"\\n{'='*80}")
        print("💰 Analysis Complete!")
        print("⚠️  IMPORTANT:")
        print("   • All 10 items are from the same collection for valid trade-ups")
        print("   • Verify current market prices before purchasing")
        print("   • Trade-up outcomes have random float values")
        print("   • Market conditions change rapidly")

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
    print("🎯 CS2 Collection-Based Trade-Up Finder")
    print("Finding profitable trade-ups using real market data...")
    
    # Load API key
    api_key = load_api_key()
    if not api_key:
        print("❌ Could not load PriceEmpire API key")
        return
    
    print(f"✅ API key loaded: {api_key[:12]}...")
    
    # Initialize finder
    finder = ImprovedTradeUpFinder(api_key)    # Configuration optimized for real trade-ups
    print("\\n⚙️  Configuration:")
    max_price_per_item = 3.00  # Higher limit for more options
    min_profit = 0.50          # Lower minimum to find any opportunities
    max_budget = 25.00         # Higher budget for realistic trade-ups
    max_results = 10
    
    print(f"  Max price per item: ${max_price_per_item:.2f}")
    print(f"  Min profit required: ${min_profit:.2f}")
    print(f"  Max total budget: ${max_budget:.2f}")
    print(f"  Max results to show: {max_results}")
    
    # Run analysis
    try:
        finder.run_analysis(max_price_per_item, min_profit, max_budget, max_results)
    except KeyboardInterrupt:
        print("\\n👋 Analysis interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
