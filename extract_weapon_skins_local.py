#!/usr/bin/env python3
"""
Extract weapon skins from fallback database to build comprehensive skin mappings.
This version uses only the local fallback database for testing.
"""

import asyncio
import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Set
import sys
from pathlib import Path

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
    """Return a comprehensive list of common CS2 weapon skins from known data"""
    print("🔄 Using fallback weapon skins database...")
    
    # Common weapon skins that are frequently traded
    fallback_skins = [
        # AK-47 skins
        "AK-47 | Redline", "AK-47 | Case Hardened", "AK-47 | Fire Serpent", "AK-47 | Vulcan",
        "AK-47 | Asiimov", "AK-47 | Wasteland Rebel", "AK-47 | Bloodsport", "AK-47 | Neon Rider",
        "AK-47 | Phantom Disruptor", "AK-47 | The Empress", "AK-47 | Inheritance", "AK-47 | Legion of Anubis",
        "AK-47 | Slate", "AK-47 | Point Disarray", "AK-47 | Frontside Misty", "AK-47 | Aquamarine Revenge",
        
        # M4A4 skins
        "M4A4 | Howl", "M4A4 | Asiimov", "M4A4 | Dragon King", "M4A4 | Royal Paladin",
        "M4A4 | Desolate Space", "M4A4 | The Emperor", "M4A4 | Neo-Noir", "M4A4 | Hellfire",
        "M4A4 | Buzz Kill", "M4A4 | 龍王 (Dragon King)", "M4A4 | X-Ray", "M4A4 | Temukau",
        
        # M4A1-S skins
        "M4A1-S | Knight", "M4A1-S | Hot Rod", "M4A1-S | Hyper Beast", "M4A1-S | Golden Coil",
        "M4A1-S | Chantico's Fire", "M4A1-S | Player Two", "M4A1-S | Printstream", "M4A1-S | Blue Phosphor",
        "M4A1-S | Cyrex", "M4A1-S | Icarus Fell", "M4A1-S | Mecha Industries", "M4A1-S | Decimator",
        
        # AWP skins
        "AWP | Dragon Lore", "AWP | Lightning Strike", "AWP | Asiimov", "AWP | Hyper Beast",
        "AWP | Redline", "AWP | Electric Hive", "AWP | Man-o'-war", "AWP | Chromatic Aberration",
        "AWP | Fade", "AWP | Gungnir", "AWP | The Prince", "AWP | Containment Breach",
        "AWP | Neo-Noir", "AWP | Oni Taiji", "AWP | Wildfire", "AWP | BOOM",
        
        # Glock-18 skins
        "Glock-18 | Fade", "Glock-18 | Water Elemental", "Glock-18 | Twilight Galaxy",
        "Glock-18 | Neo-Noir", "Glock-18 | Vogue", "Glock-18 | Moonrise",
        "Glock-18 | Dragon Tattoo", "Glock-18 | Wasteland Rebel", "Glock-18 | Bullet Queen",
        
        # USP-S skins
        "USP-S | Kill Confirmed", "USP-S | Neo-Noir", "USP-S | Orion", "USP-S | Cortex",
        "USP-S | Printstream", "USP-S | The Traitor", "USP-S | Caiman", "USP-S | Serum",
        
        # Desert Eagle skins
        "Desert Eagle | Blaze", "Desert Eagle | Printstream", "Desert Eagle | Code Red",
        "Desert Eagle | Kumicho Dragon", "Desert Eagle | Cobalt Disruption", "Desert Eagle | Mecha Industries",
        "Desert Eagle | Hypnotic", "Desert Eagle | Golden Koi", "Desert Eagle | Conspiracy",
        
        # P250 skins
        "P250 | See Ya Later", "P250 | Asiimov", "P250 | Nuclear Threat", "P250 | Muertos",
        "P250 | Undertow", "P250 | Whiteout", "P250 | Cartel", "P250 | Franklin",
        
        # Five-SeveN skins
        "Five-SeveN | Case Hardened", "Five-SeveN | Hyper Beast", "Five-SeveN | Monkey Business",
        "Five-SeveN | Fowl Play", "Five-SeveN | Copper Galaxy", "Five-SeveN | Retrobution",
        
        # Tec-9 skins
        "Tec-9 | Fuel Injector", "Tec-9 | Nuclear Threat", "Tec-9 | Bamboozle",
        "Tec-9 | Titanium Bit", "Tec-9 | Red Quartz", "Tec-9 | Ice Cap",
        
        # CZ75-Auto skins
        "CZ75-Auto | The Fuschia Is Now", "CZ75-Auto | Red Astor", "CZ75-Auto | Emerald Quartz",
        "CZ75-Auto | Victoria", "CZ75-Auto | Chalice", "CZ75-Auto | Xiangliu",
        
        # R8 Revolver skins
        "R8 Revolver | Fade", "R8 Revolver | Llama Cannon", "R8 Revolver | Amber Fade",
        "R8 Revolver | Crimson Web", "R8 Revolver | Survivalist", "R8 Revolver | Grip",
        
        # MAC-10 skins
        "MAC-10 | Neon Rider", "MAC-10 | Heat", "MAC-10 | Disco Tech",
        "MAC-10 | Curse", "MAC-10 | Fade", "MAC-10 | Stalker",
        
        # MP9 skins
        "MP9 | Hypnotic", "MP9 | Hot Rod", "MP9 | Starlight Protector",
        "MP9 | Bulldozer", "MP9 | Rose Iron", "MP9 | Wild Lily",
        
        # MP7 skins
        "MP7 | Nemesis", "MP7 | Fade", "MP7 | Bloodsport",
        "MP7 | Whiteout", "MP7 | Skulls", "MP7 | Impire",
        
        # UMP-45 skins
        "UMP-45 | Primal Saber", "UMP-45 | Arctic Wolf", "UMP-45 | Momentum",
        "UMP-45 | Blaze", "UMP-45 | Crime Scene", "UMP-45 | Grand Prix",
        
        # P90 skins
        "P90 | Asiimov", "P90 | Death by Kitty", "P90 | Dragon King", "P90 | Emerald Dragon",
        "P90 | Trigon", "P90 | Cold Blooded", "P90 | Shallow Grave", "P90 | Nostalgia",
        
        # PP-Bizon skins
        "PP-Bizon | Judgement of Anubis", "PP-Bizon | High Roller", "PP-Bizon | Fuel Rod",
        "PP-Bizon | Antique", "PP-Bizon | Blue Streak", "PP-Bizon | Osiris",
        
        # FAMAS skins
        "FAMAS | Roll Cage", "FAMAS | Afterimage", "FAMAS | Eye of Athena",
        "FAMAS | Djinn", "FAMAS | Valence", "FAMAS | Neural Net",
        
        # Galil AR skins
        "Galil AR | Cerberus", "Galil AR | Chatterbox", "Galil AR | Phoenix Blacklight",
        "Galil AR | Eco", "Galil AR | Stone Cold", "Galil AR | Chromatic Aberration",
        
        # AUG skins
        "AUG | Chameleon", "AUG | Akihabara Accept", "AUG | Flame Jörmungandr",
        "AUG | Bengal Tiger", "AUG | Hot Rod", "AUG | Syd Mead",
        
        # SG 553 skins
        "SG 553 | Integrale", "SG 553 | Danger Close", "SG 553 | Dragon Tech",
        "SG 553 | Cyrex", "SG 553 | Bulldozer", "SG 553 | Atlas",
        
        # SCAR-20 skins
        "SCAR-20 | Crimson Web", "SCAR-20 | Cardiac", "SCAR-20 | Fragments",
        "SCAR-20 | Cyrex", "SCAR-20 | Bloodsport", "SCAR-20 | Emerald",
        
        # G3SG1 skins
        "G3SG1 | Chronos", "G3SG1 | The Executioner", "G3SG1 | Scavenger",
        "G3SG1 | Flux", "G3SG1 | Azure Zebra", "G3SG1 | Dream Glade",
        
        # Nova skins
        "Nova | Hyper Beast", "Nova | Bloomstick", "Nova | Toy Soldier",
        "Nova | Antique", "Nova | Koi", "Nova | Graphite",
        
        # XM1014 skins
        "XM1014 | Tranquility", "XM1014 | Entombed", "XM1014 | Zombie Offensive",
        "XM1014 | Teclu Burner", "XM1014 | Seasons", "XM1014 | Blaze Orange",
        
        # Sawed-Off skins
        "Sawed-Off | The Kraken", "Sawed-Off | Limelight", "Sawed-Off | Wasteland Princess",
        "Sawed-Off | Serenity", "Sawed-Off | Orange DDPAT", "Sawed-Off | Brake Light",
        
        # MAG-7 skins
        "MAG-7 | Bulldozer", "MAG-7 | Cinquedea", "MAG-7 | Justice",
        "MAG-7 | Prism Terrace", "MAG-7 | Heat", "MAG-7 | Counter Terrace",
        
        # M249 skins
        "M249 | Aztec", "M249 | Deep Relief", "M249 | Emerald Poison Dart",
        "M249 | System Lock", "M249 | Spectre", "M249 | Jungle DDPAT",
        
        # Negev skins
        "Negev | Power Loader", "Negev | Mjölnir", "Negev | Lionfish",
        "Negev | Loudmouth", "Negev | Dazzle", "Negev | Man-o'-war"
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

def main():
    """Main function"""
    print("🔫 CS2 Weapon Skin Extraction Tool")
    print("=" * 50)
    
    # Get fallback items (this would normally be from API calls)
    items = get_fallback_weapon_skins()
    
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
        f.write(f"""# Auto-generated weapon skin mappings from CS2 Trade Up Calculator
# Total weapons: {len(weapon_counts)}
# Total unique skins: {sum(len(set(skins)) for skins in weapon_skins.values())}

WEAPON_SKIN_MAPPINGS = {{
{mapping_code}
}}

# Instructions:
# 1. Replace 'UNKNOWN_COLLECTION' with the actual collection name (e.g., 'Chroma 2 Case')
# 2. Replace 'UNKNOWN_RARITY' with the actual rarity (e.g., 'Mil-Spec Grade', 'Restricted', 'Classified', 'Covert', 'Contraband')
# 3. Research each skin to find its correct collection and rarity
# 4. Update the main skin_mapping.py file with these mappings
""")
    
    print(f"\n💾 Mapping code saved to: {output_file}")
    print(f"🎯 Next steps:")
    print(f"  1. Review the generated mappings")
    print(f"  2. Research and fill in correct collection and rarity information")
    print(f"  3. Update skin_mapping.py with the new mappings")
    
    # Show some sample mappings needed
    print(f"\n📋 Sample mappings generated (first 10):")
    count = 0
    for weapon in sorted(weapon_skins.keys()):
        if count >= 5:
            break
        skins = sorted(set(weapon_skins[weapon]))[:2]  # First 2 skins per weapon
        for skin in skins:
            print(f'  "{weapon} | {skin}": ("COLLECTION", "RARITY"),')
            count += 1

if __name__ == "__main__":
    main()
