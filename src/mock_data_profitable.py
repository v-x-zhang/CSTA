"""
Mock data generator with profitable trade-up scenarios for testing.
This creates a realistic scenario where some trade-ups are actually profitable.
"""

from typing import List
from decimal import Decimal
from .models import Skin

def generate_profitable_mock_skins() -> List[Skin]:
    """Generate mock skin data with profitable trade-up opportunities"""
    
    mock_skins = [
        # ================================
        # The Profitable Collection
        # ================================
        # Very cheap Mil-Spec skins (10 @ $0.50 each = $5.00 total)
        Skin(
            name="P2000 | Granite Marbleized",
            collection="The Profitable Collection", 
            rarity="Mil-Spec",
            price=Decimal("0.50"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="FAMAS | Colony",
            collection="The Profitable Collection",
            rarity="Mil-Spec",
            price=Decimal("0.52"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Galil AR | Hunting Blind",
            collection="The Profitable Collection",
            rarity="Mil-Spec",
            price=Decimal("0.48"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="MP7 | Forest DDPAT",
            collection="The Profitable Collection", 
            rarity="Mil-Spec",
            price=Decimal("0.45"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="UMP-45 | Urban DDPAT",
            collection="The Profitable Collection",
            rarity="Mil-Spec",
            price=Decimal("0.47"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Nova | Forest Leaves",
            collection="The Profitable Collection",
            rarity="Mil-Spec",
            price=Decimal("0.49"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="MAC-10 | Tornado",
            collection="The Profitable Collection",
            rarity="Mil-Spec",
            price=Decimal("0.51"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Sawed-Off | Forest DDPAT",
            collection="The Profitable Collection",
            rarity="Mil-Spec", 
            price=Decimal("0.46"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="PP-Bizon | Forest Leaves",
            collection="The Profitable Collection",
            rarity="Mil-Spec",
            price=Decimal("0.53"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="M249 | Contrast Spray",
            collection="The Profitable Collection",
            rarity="Mil-Spec",
            price=Decimal("0.44"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        
        # Expensive Restricted skins (guaranteed profit if you get any of these)
        Skin(
            name="AK-47 | Redline",
            collection="The Profitable Collection",
            rarity="Restricted",
            price=Decimal("25.00"),  # Much higher than $5 input cost
            float_min=0.10,
            float_max=0.70,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="AWP | Redline",
            collection="The Profitable Collection", 
            rarity="Restricted",
            price=Decimal("18.50"),  # Still profitable
            float_min=0.10,
            float_max=0.70,
            marketable=True,
            stattrak=False
        ),
        
        # ================================
        # The Mixed Collection  
        # ================================
        # More Mil-Spec options
        Skin(
            name="Glock-18 | Death Rattle",
            collection="The Mixed Collection",
            rarity="Mil-Spec",
            price=Decimal("0.65"),
            float_min=0.00,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="USP-S | Forest Leaves",
            collection="The Mixed Collection",
            rarity="Mil-Spec",
            price=Decimal("0.58"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="P90 | Storm",
            collection="The Mixed Collection",
            rarity="Mil-Spec",
            price=Decimal("0.72"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        
        # Mid-priced Restricted skins  
        Skin(
            name="M4A4 | Desert-Strike",
            collection="The Mixed Collection",
            rarity="Restricted",
            price=Decimal("8.50"),  # Break-even territory
            float_min=0.00,
            float_max=0.50,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Desert Eagle | Pilot",
            collection="The Mixed Collection",
            rarity="Restricted",
            price=Decimal("12.25"),  # Might be profitable
            float_min=0.00,
            float_max=0.40,
            marketable=True,
            stattrak=False
        ),
        
        # ================================
        # The Unprofitable Collection
        # ================================
        # Expensive Mil-Spec skins
        Skin(
            name="AK-47 | Elite Build",
            collection="The Unprofitable Collection",
            rarity="Mil-Spec",
            price=Decimal("2.50"),  # Too expensive for profitable trade-ups
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="M4A1-S | Basilisk",
            collection="The Unprofitable Collection",
            rarity="Mil-Spec",
            price=Decimal("2.80"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        
        # Cheap Restricted skins (making trade-ups unprofitable)
        Skin(
            name="Five-SeveN | Case Hardened",
            collection="The Unprofitable Collection",
            rarity="Restricted",
            price=Decimal("3.25"),  # 10 × $2.50 = $25, output only worth $3.25
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        
        # ================================
        # Higher tier skins for completeness
        # ================================
        Skin(
            name="AWP | Lightning Strike",
            collection="The Profitable Collection",
            rarity="Classified",
            price=Decimal("55.00"),
            float_min=0.00,
            float_max=0.08,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="AK-47 | Case Hardened",
            collection="The Mixed Collection",
            rarity="Classified", 
            price=Decimal("42.50"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="M4A4 | Howl",
            collection="The Profitable Collection",
            rarity="Covert",
            price=Decimal("2500.00"),
            float_min=0.00,
            float_max=0.50,
            marketable=True,
            stattrak=False
        ),
    ]
    
    return mock_skins
