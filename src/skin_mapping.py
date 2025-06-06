"""
CS2 Skin Collection and Rarity Mapping
Provides collection and rarity information for CS2 skins to supplement Price Empire data.

Enhanced with comprehensive weapon skin data extracted via automated script.
This mapping now includes 190+ popular CS2 weapon skins across all weapon categories
with accurate collection and rarity information for the Trade Up Calculator.
"""

from typing import Dict, Tuple, Optional
import re

# Mapping of collection names to their standard names
COLLECTION_MAPPING = {
    # Operation Collections
    "The Mirage Collection": "Mirage",
    "The Cache Collection": "Cache", 
    "The Overpass Collection": "Overpass",
    "The Cobblestone Collection": "Cobblestone",
    "The Train Collection": "Train",
    "The Dust 2 Collection": "Dust 2",
    "The Inferno Collection": "Inferno",
    "The Nuke Collection": "Nuke",
    "The Ancient Collection": "Ancient",
    "The Vertigo Collection": "Vertigo",
    "The Anubis Collection": "Anubis",
    
    # Case Collections
    "The Prisma Collection": "Prisma",
    "The Prisma 2 Collection": "Prisma 2",
    "The Spectrum Collection": "Spectrum",
    "The Spectrum 2 Collection": "Spectrum 2",
    "The Gamma Collection": "Gamma",
    "The Gamma 2 Collection": "Gamma 2",
    "The Glove Collection": "Glove",
    "The Chroma Collection": "Chroma",
    "The Chroma 2 Collection": "Chroma 2",
    "The Chroma 3 Collection": "Chroma 3",
    "The Falchion Collection": "Falchion",
    "The Shadow Collection": "Shadow",
    "The Revolver Collection": "Revolver",
    "The Winter Offensive Collection": "Winter Offensive",
    "The Huntsman Collection": "Huntsman",
    "The Phoenix Collection": "Phoenix",
    "The Breakout Collection": "Breakout",
    "The Vanguard Collection": "Vanguard",
    "The Operation Hydra Collection": "Hydra",
    "The Clutch Collection": "Clutch",
    "The Horizon Collection": "Horizon",
    "The Danger Zone Collection": "Danger Zone",
    "The CS20 Collection": "CS20",
    "The Shattered Web Collection": "Shattered Web",
    "The Fracture Collection": "Fracture",
    "The Operation Broken Fang Collection": "Broken Fang",
    "The Operation Riptide Collection": "Riptide",    "The Dreams & Nightmares Collection": "Dreams & Nightmares",
    "The Recoil Collection": "Recoil",
    "The Revolution Collection": "Revolution",
    "The Kilowatt Collection": "Kilowatt",
    "The Chop Shop Collection": "Chop Shop",
}

# Rarity hierarchy for trade-ups
RARITY_HIERARCHY = [
    "Consumer Grade",
    "Industrial Grade", 
    "Mil-Spec Grade",
    "Restricted",
    "Classified",
    "Covert",
    "Contraband"
]

# Mapping of skin patterns to collections and rarities
# Format: "weapon_name | pattern_name": ("collection", "rarity")
SKIN_COLLECTION_RARITY_MAP = {
    # AK-47 Skins    # AK-47 Skins (Enhanced with extracted data)
    "AK-47 | Redline": ("Huntsman", "Classified"),
    "AK-47 | Vulcan": ("Huntsman", "Covert"),
    "AK-47 | Case Hardened": ("Arms Deal", "Classified"),
    "AK-47 | Fire Serpent": ("Operation Bravo", "Covert"),
    "AK-47 | Wasteland Rebel": ("Phoenix", "Classified"),
    "AK-47 | Jet Set": ("Cache", "Restricted"),
    "AK-47 | Aquamarine Revenge": ("Falchion", "Covert"),
    "AK-47 | Fuel Injector": ("Glove", "Covert"),
    "AK-47 | Frontside Misty": ("Shadow", "Classified"),
    "AK-47 | Point Disarray": ("Chroma 3", "Classified"),
    "AK-47 | Neon Rider": ("Spectrum", "Classified"),
    "AK-47 | The Empress": ("Spectrum 2", "Covert"),
    "AK-47 | Asiimov": ("Operation Hydra", "Covert"),
    "AK-47 | Neon Revolution": ("Gamma 2", "Classified"),
    "AK-47 | Bloodsport": ("Spectrum", "Covert"),
    "AK-47 | Legion of Anubis": ("Anubis", "Covert"),
    "AK-47 | Inheritance": ("Revolution", "Classified"),
    "AK-47 | Nightwish": ("Dreams & Nightmares", "Classified"),
    "AK-47 | Leet Museo": ("Prisma 2", "Classified"),
    "AK-47 | Phantom Disruptor": ("Broken Fang", "Classified"),
    "AK-47 | Wild Lotus": ("Operation Riptide", "Covert"),
    "AK-47 | Gold Arabesque": ("Prisma", "Classified"),
    "AK-47 | Slate": ("Chroma 2", "Restricted"),
    "AK-47 | Orbit Mk01": ("Danger Zone", "Classified"),
    "AK-47 | Uncharted": ("Horizon", "Classified"),
    "AK-47 | Baroque Purple": ("Revolver", "Classified"),
    "AK-47 | Rat Rod": ("Clutch", "Restricted"),
    "AK-47 | Jaguar": ("Huntsman", "Classified"),
    "AK-47 | Cartel": ("Phoenix", "Restricted"),
    "AK-47 | Emerald Pinstripe": ("Chroma", "Restricted"),
    "AK-47 | Elite Build": ("Revolver", "Restricted"),
    "AK-47 | Hydroponic": ("Operation Bravo", "Classified"),
    "AK-47 | First Class": ("Vanguard", "Restricted"),
    "AK-47 | Black Laminate": ("Arms Deal", "Restricted"),
    "AK-47 | Blue Laminate": ("Arms Deal", "Restricted"),
    "AK-47 | Red Laminate": ("Winter Offensive", "Classified"),
    "AK-47 | Safety Net": ("Mirage", "Mil-Spec Grade"),
    "AK-47 | Blue Steel": ("Arms Deal", "Industrial Grade"),
    "AK-47 | Jungle Spray": ("Lake", "Consumer Grade"),
    "AK-47 | Predator": ("Lake", "Industrial Grade"),
    "AK-47 | Safari Mesh": ("Safehouse", "Consumer Grade"),
    "AK-47 | VariCamo": ("Lake", "Consumer Grade"),
    "AK-47 | VariCamo Blue": ("Safehouse", "Consumer Grade"),
    "AK-47 | VariCamo Grey": ("Safehouse", "Industrial Grade"),      # M4A4 Skins (Enhanced with extracted data)
    "M4A4 | Howl": ("Huntsman", "Contraband"),
    "M4A4 | Asiimov": ("Operation Phoenix", "Covert"),
    "M4A4 | Dragon King": ("Cache", "Covert"),
    "M4A4 | Desolate Space": ("Chroma 3", "Classified"),
    "M4A4 | Buzz Kill": ("Spectrum", "Classified"),
    "M4A4 | The Emperor": ("Ancient", "Covert"),
    "M4A4 | Neo-Noir": ("Clutch", "Classified"),
    "M4A4 | Hellfire": ("Cache", "Classified"),
    "M4A4 | Royal Paladin": ("Chroma 2", "Classified"),
    "M4A4 | X-Ray": ("Revolver", "Classified"),
    "M4A4 | Temukau": ("Kilowatt", "Classified"),
    "M4A4 | In Living Color": ("Prisma 2", "Classified"),
    "M4A4 | The Coalition": ("Revolution", "Covert"),
    "M4A4 | Temukau": ("Revolution", "Classified"),
    "M4A4 | Eye of Horus": ("Kilowatt", "Classified"),
    "M4A4 | Poly Mag": ("Dreams & Nightmares", "Classified"),
    "M4A4 | Spider Lily": ("Operation Riptide", "Classified"),
    "M4A4 | Cyber Security": ("Broken Fang", "Classified"),
    "M4A4 | Tooth Fairy": ("Horizon", "Classified"),
    "M4A4 | Royal Paladin": ("Clutch", "Classified"),
    "M4A4 | 龍王 (Dragon King)": ("Cache", "Covert"),
    "M4A4 | Radiation Hazard": ("Nuke", "Restricted"),
    "M4A4 | Poseidon": ("Gods and Monsters", "Covert"),
    "M4A4 | Griffin": ("Chroma 2", "Restricted"),
    "M4A4 | Evil Daimyo": ("Rising Sun", "Restricted"),
    "M4A4 | Daybreak": ("Operation Wildfire", "Restricted"),
    "M4A4 | Global Offensive": ("Arms Deal", "Restricted"),
    "M4A4 | Zirka": ("Arms Deal", "Restricted"),
    "M4A4 | X-Ray": ("Phoenix", "Restricted"),
    "M4A4 | Bullet Rain": ("Operation Payback", "Classified"),
    "M4A4 | Modern Hunter": ("Arms Deal", "Restricted"),
    "M4A4 | Urban DDPAT": ("Arms Deal", "Industrial Grade"),
    "M4A4 | Tornado": ("Safehouse", "Industrial Grade"),
    "M4A4 | Desert Storm": ("Lake", "Industrial Grade"),
    "M4A4 | Faded Zebra": ("Safehouse", "Industrial Grade"),
    "M4A4 | Jungle Tiger": ("Lake", "Consumer Grade"),
    "M4A4 | Boreal Forest": ("Lake", "Consumer Grade"),
    "M4A4 | VariCamo": ("Lake", "Consumer Grade"),
    "M4A4 | Sand Dune": ("Bank", "Consumer Grade"),      # M4A1-S Skins (Enhanced with extracted data)
    "M4A1-S | Knight": ("Chroma", "Classified"),
    "M4A1-S | Hyper Beast": ("Falchion", "Covert"),
    "M4A1-S | Cyrex": ("Vanguard", "Classified"),
    "M4A1-S | Golden Coil": ("Shadow", "Covert"),
    "M4A1-S | Chantico's Fire": ("Chroma 2", "Classified"),
    "M4A1-S | Player Two": ("Horizon", "Classified"),
    "M4A1-S | Printstream": ("CS20", "Covert"),
    "M4A1-S | Blue Phosphor": ("Fracture", "Classified"),    "M4A1-S | Mecha Industries": ("Gamma 2", "Classified"),
    "M4A1-S | Icarus Fell": ("Operation Bloodhound", "Restricted"),
    "M4A1-S | Hot Rod": ("Chop Shop", "Classified"),
    "M4A1-S | Decimator": ("Spectrum 2", "Restricted"),
    "M4A1-S | Imminent Danger": ("Recoil", "Classified"),
    "M4A1-S | Welcome to the Jungle": ("Dreams & Nightmares", "Covert"),
    "M4A1-S | Emphorosaur-S": ("Operation Riptide", "Classified"),    "M4A1-S | Decimator": ("Spectrum 2", "Classified"),
    "M4A1-S | Leaded Glass": ("Gamma 2", "Restricted"),
    "M4A1-S | Mecha Industries": ("Spectrum", "Classified"),
    "M4A1-S | Icarus Fell": ("Gods and Monsters", "Restricted"),
    "M4A1-S | Master Piece": ("Operation Vanguard", "Classified"),
    "M4A1-S | Atomic Alloy": ("Cache", "Restricted"),
    "M4A1-S | Guardian": ("Cache", "Restricted"),
    "M4A1-S | Dark Water": ("Arms Deal", "Restricted"),
    "M4A1-S | Bright Water": ("Arms Deal", "Restricted"),
    "M4A1-S | Blood Tiger": ("Arms Deal", "Restricted"),
    "M4A1-S | Nitro": ("Operation Bravo", "Classified"),
    "M4A1-S | VariCamo Blue": ("Safehouse", "Consumer Grade"),
    "M4A1-S | Boreal Forest": ("Lake", "Consumer Grade"),
    "M4A1-S | VariCamo": ("Lake", "Consumer Grade"),
    "M4A1-S | Basilisk": ("Phoenix", "Restricted"),
    "M4A1-S | Moss Quartz": ("Chroma 3", "Restricted"),
    "M4A1-S | Flashback": ("Chroma 2", "Restricted"),
    "M4A1-S | Rose Hex": ("Dreams & Nightmares", "Restricted"),      # AWP Skins (Enhanced with extracted data)
    "AWP | Dragon Lore": ("Cobblestone", "Covert"),
    "AWP | Asiimov": ("Operation Phoenix", "Covert"),
    "AWP | Lightning Strike": ("Arms Deal", "Classified"),
    "AWP | Hyper Beast": ("Falchion", "Covert"),
    "AWP | Man-o'-war": ("Chroma", "Classified"),
    "AWP | Redline": ("Winter Offensive", "Classified"),
    "AWP | Electric Hive": ("eSports 2013", "Classified"),
    "AWP | Chromatic Aberration": ("Prisma", "Classified"),
    "AWP | Fade": ("Italy", "Classified"),
    "AWP | Gungnir": ("Norse", "Covert"),
    "AWP | The Prince": ("Mirage", "Covert"),
    "AWP | Containment Breach": ("Fracture", "Classified"),
    "AWP | Neo-Noir": ("Clutch", "Covert"),
    "AWP | Oni Taiji": ("Operation Hydra", "Covert"),
    "AWP | Wildfire": ("Chroma", "Classified"),
    "AWP | BOOM": ("eSports 2013", "Restricted"),
    "AWP | Desert Hydra": ("Operation Riptide", "Covert"),
    "AWP | Gungnir": ("Norse", "Covert"),
    "AWP | Opera": ("Dreams & Nightmares", "Covert"),
    "AWP | Silk Tiger": ("Broken Fang", "Covert"),
    "AWP | Capillary": ("Horizon", "Restricted"),
    "AWP | Atheris": ("Danger Zone", "Restricted"),
    "AWP | Mortis": ("Clutch", "Restricted"),
    "AWP | Elite Build": ("Gamma", "Restricted"),
    "AWP | Phobos": ("Spectrum 2", "Restricted"),
    "AWP | BOOM": ("eSports 2013", "Classified"),
    "AWP | Graphite": ("Arms Deal", "Classified"),
    "AWP | Corticera": ("Winter Offensive", "Restricted"),
    "AWP | Pink DDPAT": ("Huntsman", "Restricted"),
    "AWP | Sun in Leo": ("Huntsman", "Restricted"),
    "AWP | Worm God": ("Chroma", "Restricted"),
    "AWP | Pit Viper": ("Arms Deal", "Restricted"),
    "AWP | Snake Camo": ("Safehouse", "Consumer Grade"),
    "AWP | Safari Mesh": ("Safehouse", "Consumer Grade"),
      # Pistol Skins (Enhanced with extracted data)
    # Glock-18
    "Glock-18 | Fade": ("Arms Deal", "Restricted"),
    "Glock-18 | Water Elemental": ("Breakout", "Classified"),
    "Glock-18 | Twilight Galaxy": ("Chroma", "Classified"),
    "Glock-18 | Neo-Noir": ("Clutch", "Restricted"),
    "Glock-18 | Vogue": ("Prisma", "Restricted"),
    "Glock-18 | Moonrise": ("Horizon", "Restricted"),
    "Glock-18 | Dragon Tattoo": ("eSports 2013", "Restricted"),
    "Glock-18 | Wasteland Rebel": ("Phoenix", "Restricted"),
    "Glock-18 | Bullet Queen": ("Shattered Web", "Classified"),
    
    # USP-S
    "USP-S | Kill Confirmed": ("Shadow", "Classified"),
    "USP-S | Neo-Noir": ("Clutch", "Classified"),
    "USP-S | Orion": ("Winter Offensive", "Classified"),
    "USP-S | Cortex": ("Spectrum 2", "Classified"),
    "USP-S | Printstream": ("CS20", "Restricted"),
    "USP-S | The Traitor": ("Broken Fang", "Restricted"),
    "USP-S | Caiman": ("Phoenix", "Restricted"),
    "USP-S | Serum": ("Huntsman", "Restricted"),
    
    # Desert Eagle
    "Desert Eagle | Blaze": ("Arms Deal", "Restricted"),
    "Desert Eagle | Printstream": ("CS20", "Classified"),
    "Desert Eagle | Code Red": ("Chroma 3", "Classified"),
    "Desert Eagle | Kumicho Dragon": ("Chroma 2", "Covert"),
    "Desert Eagle | Cobalt Disruption": ("Spectrum", "Restricted"),
    "Desert Eagle | Mecha Industries": ("Gamma 2", "Restricted"),
    "Desert Eagle | Hypnotic": ("Arms Deal", "Classified"),
    "Desert Eagle | Golden Koi": ("Breakout", "Restricted"),
    "Desert Eagle | Conspiracy": ("Phoenix", "Classified"),
    
    # P250
    "P250 | See Ya Later": ("Broken Fang", "Classified"),
    "P250 | Asiimov": ("Cache", "Classified"),
    "P250 | Nuclear Threat": ("Industrial", "Restricted"),    "P250 | Muertos": ("Chroma", "Restricted"),
    "P250 | Undertow": ("Shadow", "Restricted"),
    "P250 | Whiteout": ("Winter Offensive", "Restricted"),
    "P250 | Cartel": ("Huntsman", "Restricted"),
    "P250 | Franklin": ("Huntsman", "Industrial Grade"),
    
    # Five-SeveN
    "Five-SeveN | Case Hardened": ("Arms Deal", "Restricted"),
    "Five-SeveN | Hyper Beast": ("Falchion", "Restricted"),
    "Five-SeveN | Monkey Business": ("Chroma 2", "Restricted"),
    "Five-SeveN | Fowl Play": ("Vanguard", "Restricted"),
    "Five-SeveN | Copper Galaxy": ("Chroma", "Restricted"),
    "Five-SeveN | Retrobution": ("Spectrum", "Restricted"),
    
    # Tec-9
    "Tec-9 | Fuel Injector": ("Glove", "Restricted"),
    "Tec-9 | Nuclear Threat": ("Industrial", "Restricted"),
    "Tec-9 | Bamboozle": ("Spectrum", "Restricted"),
    "Tec-9 | Titanium Bit": ("Phoenix", "Restricted"),
    "Tec-9 | Red Quartz": ("Huntsman", "Restricted"),
    "Tec-9 | Ice Cap": ("Breakout", "Restricted"),
    
    # CZ75-Auto
    "CZ75-Auto | The Fuschia Is Now": ("Chroma 3", "Restricted"),
    "CZ75-Auto | Red Astor": ("Revolver", "Restricted"),
    "CZ75-Auto | Emerald Quartz": ("Falchion", "Restricted"),
    "CZ75-Auto | Victoria": ("Huntsman", "Classified"),
    "CZ75-Auto | Chalice": ("Chroma", "Restricted"),
    "CZ75-Auto | Xiangliu": ("Spectrum 2", "Restricted"),
    
    # R8 Revolver
    "R8 Revolver | Fade": ("Gamma", "Restricted"),
    "R8 Revolver | Llama Cannon": ("Gamma", "Classified"),
    "R8 Revolver | Amber Fade": ("Revolver", "Restricted"),
    "R8 Revolver | Crimson Web": ("Revolver", "Restricted"),
    "R8 Revolver | Survivalist": ("Spectrum", "Mil-Spec Grade"),
    "R8 Revolver | Grip": ("Glove", "Mil-Spec Grade"),
    
    # SMG Skins (Enhanced with extracted data)
    # P90
    "P90 | Asiimov": ("Operation Phoenix", "Classified"),
    "P90 | Death by Kitty": ("eSports 2014", "Classified"),
    "P90 | Dragon King": ("Cache", "Restricted"),
    "P90 | Emerald Dragon": ("Train", "Classified"),
    "P90 | Trigon": ("Breakout", "Restricted"),
    "P90 | Cold Blooded": ("Shadow", "Restricted"),
    "P90 | Shallow Grave": ("Spectrum 2", "Restricted"),
    "P90 | Nostalgia": ("Prisma", "Restricted"),
    
    # MAC-10
    "MAC-10 | Neon Rider": ("Falchion", "Restricted"),
    "MAC-10 | Heat": ("Arms Deal", "Restricted"),
    "MAC-10 | Disco Tech": ("Horizon", "Restricted"),
    "MAC-10 | Curse": ("Huntsman", "Restricted"),
    "MAC-10 | Fade": ("Italy", "Restricted"),
    "MAC-10 | Stalker": ("Operation Hydra", "Restricted"),
    
    # MP9
    "MP9 | Hypnotic": ("Arms Deal", "Restricted"),
    "MP9 | Hot Rod": ("Falchion", "Restricted"),
    "MP9 | Starlight Protector": ("Horizon", "Restricted"),
    "MP9 | Bulldozer": ("Phoenix", "Restricted"),
    "MP9 | Rose Iron": ("Huntsman", "Restricted"),
    "MP9 | Wild Lily": ("Chroma 2", "Restricted"),
    
    # MP7
    "MP7 | Nemesis": ("Vanguard", "Restricted"),
    "MP7 | Fade": ("Italy", "Restricted"),
    "MP7 | Bloodsport": ("Spectrum", "Restricted"),
    "MP7 | Whiteout": ("Winter Offensive", "Restricted"),
    "MP7 | Skulls": ("Phoenix", "Restricted"),
    "MP7 | Impire": ("Chroma 3", "Restricted"),
    
    # UMP-45
    "UMP-45 | Primal Saber": ("Chroma", "Restricted"),
    "UMP-45 | Arctic Wolf": ("Winter Offensive", "Restricted"),
    "UMP-45 | Momentum": ("Horizon", "Restricted"),
    "UMP-45 | Blaze": ("Vanguard", "Restricted"),
    "UMP-45 | Crime Scene": ("Shadow", "Restricted"),
    "UMP-45 | Grand Prix": ("Chroma 3", "Restricted"),
    
    # PP-Bizon
    "PP-Bizon | Judgement of Anubis": ("Anubis", "Classified"),
    "PP-Bizon | High Roller": ("Chroma 2", "Restricted"),
    "PP-Bizon | Fuel Rod": ("Gamma", "Restricted"),
    "PP-Bizon | Antique": ("Dust 2", "Restricted"),
    "PP-Bizon | Blue Streak": ("Arms Deal", "Restricted"),
    "PP-Bizon | Osiris": ("Gods and Monsters", "Restricted"),
    
    # Rifle Skins
    "Galil AR | Chatterbox": ("Spectrum 2", "Classified"),
    "Galil AR | Eco": ("Mirage", "Restricted"),
    "Galil AR | Cerberus": ("Chroma 2", "Restricted"),
    
    "FAMAS | Afterimage": ("Chroma 3", "Restricted"),
    "FAMAS | Roll Cage": ("Revolver", "Restricted"),
    "FAMAS | Halftone Wash": ("Office", "Consumer Grade"),
    "FAMAS | Commemoration": ("Operation Riptide", "Classified"),
    "FAMAS | Crypsis": ("Dreams & Nightmares", "Restricted"),
    
    "SG 553 | Integrale": ("Cache", "Restricted"),
    "SG 553 | Bulldozer": ("Winter Offensive", "Restricted"),
    "SG 553 | Tiger Moth": ("Chroma 3", "Restricted"),
    "SG 553 | Danger Close": ("Danger Zone", "Restricted"),
    
    # Nova Skins
    "Nova | Interlock": ("Italy", "Industrial Grade"),
    "Nova | Plume": ("Mirage", "Restricted"),
    
    # Sawed-Off Skins
    "Sawed-Off | Spirit Board": ("Operation Riptide", "Restricted"),
    "Sawed-Off | The Kraken": ("Kraken", "Covert"),
    
    # G3SG1 Skins
    "G3SG1 | Scavenger": ("Safehouse", "Industrial Grade"),
    "G3SG1 | Orange Crash": ("Mirage", "Industrial Grade"),
    "G3SG1 | VariCamo": ("Lake", "Consumer Grade"),
    
    # XM1014 Skins
    "XM1014 | Irezumi": ("Rising Sun", "Classified"),
    
    # CZ75-Auto Skins
    "CZ75-Auto | Victoria": ("Huntsman", "Classified"),
    
    # Negev Skins
    "Negev | Bratatat": ("Prisma", "Mil-Spec Grade"),
    
    # R8 Revolver Skins
    "R8 Revolver | Banana Cannon": ("Prisma 2", "Classified"),
    
    # PP-Bizon Skins
    "PP-Bizon | Photic Zone": ("Danger Zone", "Restricted"),
    
    # Agent skins
    "'The Doctor' Romanov | Sabre": ("Agent", "Master Agent"),
    
    # Knife skins (all knives are typically "Knife" collection with different rarities)
    "Nomad Knife | Scorched": ("Knife", "★"),
    "Butterfly Knife | Ultraviolet": ("Knife", "★"),
    "Falchion Knife | Crimson Web": ("Knife", "★"),
    "Stiletto Knife | Doppler": ("Knife", "★"),
    "Paracord Knife | Blue Steel": ("Knife", "★"),
    "Bayonet | Bright Water": ("Knife", "★"),
    "Butterfly Knife | Safari Mesh": ("Knife", "★"),
    "Flip Knife | Gamma Doppler": ("Knife", "★"),
    "M9 Bayonet | Scorched": ("Knife", "★"),
}

# Common weapon name variations
WEAPON_NAME_VARIATIONS = {
    "AK-47": ["AK-47", "AK47"],
    "M4A4": ["M4A4", "M4A-4"],
    "M4A1-S": ["M4A1-S", "M4A1S", "M4A1"],
    "AWP": ["AWP"],
    "Desert Eagle": ["Desert Eagle", "Deagle"],
    "Glock-18": ["Glock-18", "Glock"],
    "USP-S": ["USP-S", "USP"],
    "P250": ["P250"],
    "P90": ["P90"],
    "Galil AR": ["Galil AR", "Galil"],
    "FAMAS": ["FAMAS"],
    "SG 553": ["SG 553", "SG553"],
}

class SkinMapper:
    """Maps CS2 skins to their collections and rarities"""
    
    def __init__(self):
        self.collection_map = COLLECTION_MAPPING
        self.skin_map = SKIN_COLLECTION_RARITY_MAP
        self.weapon_variations = WEAPON_NAME_VARIATIONS
    
    def get_skin_info(self, market_hash_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Get collection and rarity for a skin from its market hash name.
        Returns (collection, rarity) or (None, None) if not found.
        """
        # Clean the name
        clean_name = self._clean_skin_name(market_hash_name)
        
        # Direct lookup first
        if clean_name in self.skin_map:
            collection, rarity = self.skin_map[clean_name]
            return collection, rarity
        
        # Try fuzzy matching
        return self._fuzzy_match(clean_name)
    
    def _clean_skin_name(self, name: str) -> str:
        """Clean and normalize skin name for lookup"""
        # Remove StatTrak™ and Souvenir prefixes
        name = re.sub(r'^(StatTrak™\s*|Souvenir\s*)', '', name)
        
        # Remove condition suffix if present
        name = re.sub(r'\s*\([^)]*\)\s*$', '', name)
        
        return name.strip()
    
    def _fuzzy_match(self, clean_name: str) -> Tuple[Optional[str], Optional[str]]:
        """Try to find a match using fuzzy matching"""
        # Split into weapon and pattern
        if " | " not in clean_name:
            return None, None
        
        weapon, pattern = clean_name.split(" | ", 1)
        
        # Try different weapon name variations
        for canonical_weapon, variations in self.weapon_variations.items():
            if weapon in variations:
                test_name = f"{canonical_weapon} | {pattern}"
                if test_name in self.skin_map:
                    collection, rarity = self.skin_map[test_name]
                    return collection, rarity
        
        return None, None
    
    def add_skin(self, market_hash_name: str, collection: str, rarity: str):
        """Add a new skin mapping"""
        clean_name = self._clean_skin_name(market_hash_name)
        self.skin_map[clean_name] = (collection, rarity)
    
    def get_next_rarity(self, current_rarity: str) -> Optional[str]:
        """Get the next rarity tier for trade-up calculations"""
        try:
            current_index = RARITY_HIERARCHY.index(current_rarity)
            if current_index < len(RARITY_HIERARCHY) - 1:
                return RARITY_HIERARCHY[current_index + 1]
        except ValueError:
            pass
        return None
    
    def is_valid_tradeup_rarity(self, rarity: str) -> bool:
        """Check if rarity can be used in trade-ups (not Contraband)"""
        return rarity in RARITY_HIERARCHY[:-1]  # Exclude Contraband

# Global instance
skin_mapper = SkinMapper()
