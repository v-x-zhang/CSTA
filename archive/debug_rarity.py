#!/usr/bin/env python3
"""
Debug script to check rarity detection and output value calculation
"""

import json
import requests
from collections import defaultdict

# Load API key
with open('config/secrets.json', 'r') as f:
    config = json.load(f)
api_key = config['api']['priceempire_key']

headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}

def extract_rarity_from_name(item_name: str) -> str:
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

def is_tradeable_weapon(item_name: str) -> bool:
    """Check if item is a tradeable weapon/knife skin"""
    exclude_keywords = [
        'Sticker |', 'Souvenir ', 'StatTrak™ Music Kit',
        'Music Kit |', 'Graffiti |', 'Patch |', 'Case',
        'Key', 'Pass', 'Pin', 'Collectible'
    ]
    
    if any(keyword in item_name for keyword in exclude_keywords):
        return False
    
    weapon_keywords = [
        'AK-47 |', 'M4A4 |', 'M4A1-S |', 'AWP |', 'Glock-18 |',
        'USP-S |', 'P250 |', 'Tec-9 |', 'Five-SeveN |', 'CZ75-Auto |',
        'Desert Eagle |', 'Dual Berettas |', 'P2000 |', 'MAC-10 |',
        'MP9 |', 'MP7 |', 'UMP-45 |', 'P90 |', 'PP-Bizon |',
        'Nova |', 'XM1014 |', 'MAG-7 |', 'Sawed-Off |', 'M249 |',
        'Negev |', 'FAMAS |', 'Galil AR |', 'SG 553 |', 'AUG |',
        'SSG 08 |', 'SCAR-20 |', 'G3SG1 |', '★ ', 'Karambit |',
        'Bayonet |', 'Flip Knife |', 'Gut Knife |'
    ]
    
    return any(keyword in item_name for keyword in weapon_keywords)

# Get market data
print("🔍 Fetching market data...")
response = requests.get(
    'https://api.pricempire.com/v4/paid/items/prices',
    headers=headers,
    params={'app_id': 730, 'currency': 'USD', 'language': 'en'},
    timeout=30
)

if response.status_code != 200:
    print(f"❌ API Error: {response.status_code}")
    exit(1)

data = response.json()
print(f"✅ Got {len(data)} items")

# Analyze rarity distribution
rarity_counts = defaultdict(int)
pistol_items = []
sample_items = []

for item_data in data[:1000]:  # Check first 1000 items
    market_hash_name = item_data.get('market_hash_name', '')
    
    if not is_tradeable_weapon(market_hash_name):
        continue
        
    rarity = extract_rarity_from_name(market_hash_name)
    rarity_counts[rarity] += 1
    
    # Collect P250 items for detailed analysis
    if 'P250 |' in market_hash_name:
        pistol_items.append({
            'name': market_hash_name,
            'rarity': rarity,
            'prices': item_data.get('prices', [])
        })
    
    # Collect some sample items to verify our rarity detection
    if len(sample_items) < 10:
        sample_items.append({
            'name': market_hash_name,
            'rarity': rarity
        })

print(f"\n📊 Rarity Distribution (first 1000 tradeable items):")
for rarity, count in rarity_counts.items():
    print(f"   {rarity}: {count} items")

print(f"\n🔫 Sample P250 Items:")
for item in pistol_items[:10]:
    print(f"   {item['name']} → {item['rarity']}")
    # Show first price
    if item['prices']:
        first_price = item['prices'][0]
        print(f"      💰 {first_price.get('provider_key', 'unknown')}: ${first_price.get('price', 'N/A')}")

print(f"\n🎯 Sample Items Rarity Detection:")
for item in sample_items:
    print(f"   {item['name']} → {item['rarity']}")

# Check if we have any actual Restricted items
print(f"\n🔍 Looking for actual Restricted items...")
restricted_found = 0
for item_data in data[:5000]:
    market_hash_name = item_data.get('market_hash_name', '')
    if not is_tradeable_weapon(market_hash_name):
        continue
        
    # Look for items that might actually be Restricted
    if any(pattern in market_hash_name.lower() for pattern in ['redline', 'guardian', 'vulcan', 'cyrex']):
        rarity = extract_rarity_from_name(market_hash_name)
        print(f"   🎯 {market_hash_name} → {rarity}")
        restricted_found += 1
        if restricted_found >= 5:
            break

print(f"\n✅ Analysis complete!")
