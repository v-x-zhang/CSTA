#!/usr/bin/env python3
"""
Extract weapon skins from Price Empire API to build comprehensive skin mappings.
This script fetches all items and identifies weapon skins that need mapping.
"""

import asyncio
import aiohttp
import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Set
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.logging_config import setup_logging

# Setup logging
setup_logging()

# Price Empire API configuration
PRICE_EMPIRE_BASE_URL = "https://pricempire.com/api/v3"
API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Referer': 'https://pricempire.com/',
    'Origin': 'https://pricempire.com',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': '"Windows"'
}

# Weapon types that we want to map (excluding knives, stickers, cases, etc.)
WEAPON_TYPES = {
    # Rifles
    'AK-47', 'M4A4', 'M4A1-S', 'AWP', 'FAMAS', 'Galil AR', 'AUG', 'SG 553', 'SCAR-20', 'G3SG1',
    
    # Pistols
    'Glock-18', 'USP-S', 'P2000', 'P250', 'Five-SeveN', 'Tec-9', 'CZ75-Auto', 'Desert Eagle', 'Dual Berettas', 'R8 Revolver',
    
    # SMGs
    'MAC-10', 'MP9', 'MP7', 'UMP-45', 'P90', 'PP-Bizon', 'MP5-SD',
    
    # Shotguns
    'Nova', 'XM1014', 'Sawed-Off', 'MAG-7',
    
    # LMGs
    'M249', 'Negev'
}

# Items to skip (non-weapons)
SKIP_PATTERNS = [
    r'^★',  # Knives
    r'^Sticker',  # Stickers
    r'^Patch',  # Patches
    r'^Sealed Graffiti',  # Graffiti
    r'Case$',  # Cases
    r'Capsule$',  # Capsules
    r'Pin$',  # Pins
    r'Music Kit',  # Music kits
    r'Souvenir Package',  # Souvenir packages
    r"'.*'",  # Agents/characters
]

def should_skip_item(name: str) -> bool:
    """Check if item should be skipped based on patterns"""
    for pattern in SKIP_PATTERNS:
        if re.search(pattern, name):
            return True
    return False

def extract_weapon_and_skin(name: str) -> tuple:
    """Extract weapon type and skin name from market hash name"""
    # Remove StatTrak™ and Souvenir prefixes
    clean_name = re.sub(r'^(StatTrak™ |Souvenir )', '', name)
    
    # Split on | to separate weapon and skin
    parts = clean_name.split(' | ')
    if len(parts) != 2:
        return None, None
    
    weapon = parts[0].strip()
    skin_with_condition = parts[1].strip()
    
    # Remove condition from skin name
    skin = re.sub(r' \((Factory New|Minimal Wear|Field-Tested|Well-Worn|Battle-Scarred)\)$', '', skin_with_condition)
    
    return weapon, skin

def get_fallback_weapon_skins():
    """Fallback: Return a comprehensive list of common CS2 weapon skins from known data"""
    print("🔄 Using fallback weapon skins database...")
    
    # Common weapon skins that are frequently traded
    fallback_skins = [
        # AK-47 skins
        "AK-47 | Redline", "AK-47 | Case Hardened", "AK-47 | Fire Serpent", "AK-47 | Vulcan",
        "AK-47 | Asiimov", "AK-47 | Wasteland Rebel", "AK-47 | Bloodsport", "AK-47 | Neon Rider",
        "AK-47 | Phantom Disruptor", "AK-47 | The Empress", "AK-47 | Inheritance", "AK-47 | Legion of Anubis",
        
        # M4A4 skins
        "M4A4 | Howl", "M4A4 | Asiimov", "M4A4 | Dragon King", "M4A4 | Royal Paladin",
        "M4A4 | Desolate Space", "M4A4 | The Emperor", "M4A4 | Neo-Noir", "M4A4 | Hellfire",
        
        # M4A1-S skins
        "M4A1-S | Knight", "M4A1-S | Hot Rod", "M4A1-S | Hyper Beast", "M4A1-S | Golden Coil",
        "M4A1-S | Chantico's Fire", "M4A1-S | Player Two", "M4A1-S | Printstream", "M4A1-S | Blue Phosphor",
        
        # AWP skins
        "AWP | Dragon Lore", "AWP | Lightning Strike", "AWP | Asiimov", "AWP | Hyper Beast",
        "AWP | Redline", "AWP | Electric Hive", "AWP | Man-o'-war", "AWP | Chromatic Aberration",
        "AWP | Fade", "AWP | Gungnir", "AWP | The Prince", "AWP | Containment Breach",
        
        # Glock-18 skins
        "Glock-18 | Fade", "Glock-18 | Water Elemental", "Glock-18 | Twilight Galaxy",
        "Glock-18 | Neo-Noir", "Glock-18 | Vogue", "Glock-18 | Moonrise",
        
        # USP-S skins
        "USP-S | Kill Confirmed", "USP-S | Neo-Noir", "USP-S | Orion", "USP-S | Cortex",
        "USP-S | Printstream", "USP-S | The Traitor",
        
        # Desert Eagle skins
        "Desert Eagle | Blaze", "Desert Eagle | Printstream", "Desert Eagle | Code Red",
        "Desert Eagle | Kumicho Dragon", "Desert Eagle | Cobalt Disruption", "Desert Eagle | Mecha Industries",
        
        # P250 skins
        "P250 | See Ya Later", "P250 | Asiimov", "P250 | Nuclear Threat", "P250 | Muertos",
        
        # Five-SeveN skins
        "Five-SeveN | Case Hardened", "Five-SeveN | Hyper Beast", "Five-SeveN | Monkey Business",
        
        # Tec-9 skins
        "Tec-9 | Fuel Injector", "Tec-9 | Nuclear Threat", "Tec-9 | Bamboozle",
        
        # CZ75-Auto skins
        "CZ75-Auto | The Fuschia Is Now", "CZ75-Auto | Red Astor", "CZ75-Auto | Emerald Quartz",
        
        # R8 Revolver skins
        "R8 Revolver | Fade", "R8 Revolver | Llama Cannon", "R8 Revolver | Amber Fade",
        
        # MAC-10 skins
        "MAC-10 | Neon Rider", "MAC-10 | Heat", "MAC-10 | Disco Tech",
        
        # MP9 skins
        "MP9 | Hypnotic", "MP9 | Hot Rod", "MP9 | Starlight Protector",
        
        # MP7 skins
        "MP7 | Nemesis", "MP7 | Fade", "MP7 | Bloodsport",
        
        # UMP-45 skins
        "UMP-45 | Primal Saber", "UMP-45 | Arctic Wolf", "UMP-45 | Momentum",
        
        # P90 skins
        "P90 | Asiimov", "P90 | Death by Kitty", "P90 | Dragon King", "P90 | Emerald Dragon",
        
        # PP-Bizon skins
        "PP-Bizon | Judgement of Anubis", "PP-Bizon | High Roller", "PP-Bizon | Fuel Rod",
        
        # FAMAS skins
        "FAMAS | Roll Cage", "FAMAS | Afterimage", "FAMAS | Eye of Athena",
        
        # Galil AR skins
        "Galil AR | Cerberus", "Galil AR | Chatterbox", "Galil AR | Phoenix Blacklight",
        
        # AUG skins
        "AUG | Chameleon", "AUG | Akihabara Accept", "AUG | Flame Jörmungandr",
        
        # SG 553 skins
        "SG 553 | Integrale", "SG 553 | Danger Close", "SG 553 | Dragon Tech",
        
        # SCAR-20 skins
        "SCAR-20 | Crimson Web", "SCAR-20 | Cardiac", "SCAR-20 | Fragments",
        
        # G3SG1 skins
        "G3SG1 | Chronos", "G3SG1 | The Executioner", "G3SG1 | Scavenger",
        
        # Nova skins
        "Nova | Hyper Beast", "Nova | Bloomstick", "Nova | Toy Soldier",
        
        # XM1014 skins
        "XM1014 | Tranquility", "XM1014 | Entombed", "XM1014 | Zombie Offensive",
        
        # Sawed-Off skins
        "Sawed-Off | The Kraken", "Sawed-Off | Limelight", "Sawed-Off | Wasteland Princess",
        
        # MAG-7 skins
        "MAG-7 | Bulldozer", "MAG-7 | Cinquedea", "MAG-7 | Justice",
        
        # M249 skins
        "M249 | Aztec", "M249 | Deep Relief", "M249 | Emerald Poison Dart",
        
        # Negev skins
        "Negev | Power Loader", "Negev | Mjölnir", "Negev | Lionfish"
    ]
    
    # Convert to the expected format
    items = []
    for skin_name in fallback_skins:
        items.append({
            'market_hash_name': skin_name,
            'name': skin_name
        })
    
    print(f"✅ Loaded {len(items)} fallback weapon skins")
    return items
    """Fallback: Fetch weapon skins from Steam Market API"""
    print("🔄 Trying Steam Market API as fallback...")
    
    timeout = aiohttp.ClientTimeout(total=30)
    steam_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    items = []
    
    async with aiohttp.ClientSession(headers=steam_headers, timeout=timeout) as session:
        # Steam Market search for CS2 items
        base_url = "https://steamcommunity.com/market/search/render/"
        
        # Search for different weapon categories
        searches = [
            "AK-47", "M4A4", "M4A1-S", "AWP", "Glock-18", "USP-S", "Desert Eagle",
            "P250", "Five-SeveN", "Tec-9", "CZ75-Auto", "R8 Revolver"
        ]
        
        for search_term in searches:
            try:
                params = {
                    'query': search_term,
                    'start': 0,
                    'count': 100,
                    'search_descriptions': 0,
                    'sort_column': 'popular',
                    'sort_dir': 'desc',
                    'appid': 730,  # CS2 app ID
                    'norender': 1
                }
                
                print(f"🔍 Searching Steam Market for: {search_term}")
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = data.get('results', [])
                        
                        for item in results:
                            name = item.get('name', item.get('hash_name', ''))
                            if name and '|' in name:  # Only weapon skins
                                items.append({
                                    'market_hash_name': name,
                                    'name': name
                                })
                        
                        print(f"📦 Found {len(results)} items for {search_term}")
                        
                        # Rate limiting
                        await asyncio.sleep(1)
                    else:
                        print(f"❌ Steam Market search failed for {search_term}: {response.status}")
                        
            except Exception as e:
                print(f"❌ Error searching for {search_term}: {str(e)}")
                continue
    
    print(f"✅ Steam Market fallback collected {len(items)} items")
    return items
    """Fetch all items from Price Empire API"""
    print("🔄 Fetching all items from Price Empire API...")
    
    # Configure session with SSL and timeout settings
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=False)
  async def fetch_all_items():
    """Fetch all items from Price Empire API with fallback options"""
    print("🔄 Fetching all items from Price Empire API...")
    
    # Configure session with SSL and timeout settings
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(ssl=False)
    
    async with aiohttp.ClientSession(
        headers=API_HEADERS, 
        timeout=timeout, 
        connector=connector
    ) as session:
        try:
            # Try multiple endpoints/approaches
            endpoints_to_try = [
                # Main prices endpoint
                {
                    'url': f"{PRICE_EMPIRE_BASE_URL}/items/prices",
                    'params': {'language': 'en', 'limit': '50000'}
                },
                # Alternative without limit
                {
                    'url': f"{PRICE_EMPIRE_BASE_URL}/items/prices",
                    'params': {'language': 'en'}
                },
                # Try items endpoint
                {
                    'url': f"{PRICE_EMPIRE_BASE_URL}/items",
                    'params': {'language': 'en', 'limit': '50000'}
                }
            ]
            
            for endpoint_config in endpoints_to_try:
                print(f"🔗 Trying: {endpoint_config['url']} with params: {endpoint_config['params']}")
                
                try:
                    async with session.get(
                        endpoint_config['url'], 
                        params=endpoint_config['params']
                    ) as response:
                        print(f"📡 Response status: {response.status}")
                        
                        if response.status == 200:
                            content_type = response.headers.get('content-type', '')
                            print(f"📄 Content type: {content_type}")
                            
                            if 'application/json' in content_type:
                                data = await response.json()
                                
                                # Handle different response structures
                                items = []
                                if isinstance(data, dict):
                                    items = data.get('data', data.get('items', []))
                                elif isinstance(data, list):
                                    items = data
                                
                                print(f"✅ Successfully fetched {len(items)} items")
                                if items:
                                    return items
                                else:
                                    print("⚠️ No items found in response")
                            else:
                                text_content = await response.text()
                                print(f"❌ Unexpected content type. First 500 chars:")
                                print(text_content[:500])
                        else:
                            error_text = await response.text()
                            print(f"❌ HTTP {response.status}: {error_text[:200]}")
                
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout for endpoint: {endpoint_config['url']}")
                    continue
                except Exception as e:
                    print(f"❌ Error with endpoint {endpoint_config['url']}: {str(e)}")
                    continue
            
            print("❌ All Price Empire endpoints failed, trying fallback...")
            
        except Exception as e:
            print(f"❌ Session error: {str(e)}")
      # Fallback to Steam Market if Price Empire fails
    print("🔄 Falling back to Steam Market API...")
    steam_items = await fetch_from_steam_market()
    
    if steam_items:
        return steam_items
    
    # Final fallback to local database
    print("🔄 Using local fallback database...")
    return get_fallback_weapon_skins()

def analyze_weapons(items: List[dict]):
    """Analyze weapon items and categorize them"""
    weapon_skins = defaultdict(list)  # weapon_type -> [skin_names]
    weapon_counts = Counter()
    unmapped_weapons = set()
    skipped_items = []
    
    print("\n🔍 Analyzing weapon skins...")
    
    for item in items:
        name = item.get('market_hash_name', '')
        
        # Skip non-weapon items
        if should_skip_item(name):
            skipped_items.append(name)
            continue
        
        # Extract weapon and skin
        weapon, skin = extract_weapon_and_skin(name)
        
        if weapon and skin and weapon in WEAPON_TYPES:
            weapon_skins[weapon].append(skin)
            weapon_counts[weapon] += 1
        elif weapon and skin:
            unmapped_weapons.add(weapon)
    
    return weapon_skins, weapon_counts, unmapped_weapons, skipped_items

def generate_mapping_code(weapon_skins: Dict[str, List[str]]):
    """Generate Python code for skin mappings"""
    print("\n📝 Generating mapping code...")
    
    mapping_lines = []
    
    for weapon in sorted(weapon_skins.keys()):
        skins = sorted(set(weapon_skins[weapon]))  # Remove duplicates and sort
        
        mapping_lines.append(f"\n    # {weapon} Skins")
        
        for skin in skins:
            # Use placeholder collection and rarity - these need to be filled in manually
            skin_key = f"{weapon} | {skin}"
            mapping_lines.append(f'    "{skin_key}": ("UNKNOWN_COLLECTION", "UNKNOWN_RARITY"),')
    
    return '\n'.join(mapping_lines)

async def main():
    """Main function"""
    # Fetch all items
    items = await fetch_all_items()
    
    if not items:
        print("❌ No items fetched, exiting")
        return
    
    # Analyze weapons
    weapon_skins, weapon_counts, unmapped_weapons, skipped_items = analyze_weapons(items)
    
    # Print summary
    print(f"\n📊 Analysis Summary:")
    print(f"Total items analyzed: {len(items)}")
    print(f"Items skipped (non-weapons): {len(skipped_items)}")
    print(f"Weapon types found: {len(weapon_counts)}")
    print(f"Unknown weapon types: {len(unmapped_weapons)}")
    
    print(f"\n🔫 Weapon skin counts:")
    for weapon, count in weapon_counts.most_common():
        print(f"  {weapon}: {count} skins")
    
    if unmapped_weapons:
        print(f"\n❓ Unknown weapon types found:")
        for weapon in sorted(unmapped_weapons):
            print(f"  {weapon}")
    
    # Generate mapping code
    mapping_code = generate_mapping_code(weapon_skins)
    
    # Save to file
    output_file = "weapon_skin_mappings.py"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"""# Auto-generated weapon skin mappings
# Total weapons: {len(weapon_counts)}
# Total unique skins: {sum(len(set(skins)) for skins in weapon_skins.values())}

WEAPON_SKIN_MAPPINGS = {{
{mapping_code}
}}
""")
    
    print(f"\n💾 Mapping code saved to: {output_file}")
    print(f"🎯 Next steps:")
    print(f"  1. Review the generated mappings")
    print(f"  2. Research and fill in correct collection and rarity information")
    print(f"  3. Update skin_mapping.py with the new mappings")
    
    # Show some sample mappings needed
    print(f"\n📋 Sample mappings needed (first 10):")
    count = 0
    for weapon in sorted(weapon_skins.keys()):
        if count >= 5:
            break
        skins = sorted(set(weapon_skins[weapon]))[:2]  # First 2 skins per weapon
        for skin in skins:
            print(f'  "{weapon} | {skin}": ("COLLECTION", "RARITY"),')
            count += 1

if __name__ == "__main__":
    asyncio.run(main())
