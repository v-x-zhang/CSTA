"""
Mock data generator for testing the trade-up calculator without API dependencies.
"""

from typing import List
from decimal import Decimal
from .models import Skin

def generate_mock_skins() -> List[Skin]:
    """Generate mock skin data for testing"""
    
    mock_skins = [
        # The Dust 2 Collection - Mil-Spec to Covert
        Skin(
            name="AK-47 | Redline",
            collection="The Dust 2 Collection", 
            rarity="Classified",
            price=Decimal("45.00"),
            float_min=0.05,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="AWP | Redline", 
            collection="The Dust 2 Collection",
            rarity="Classified", 
            price=Decimal("38.50"),
            float_min=0.10,
            float_max=0.70,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Desert Eagle | Hypnotic",
            collection="The Dust 2 Collection",
            rarity="Restricted",
            price=Decimal("8.75"),
            float_min=0.00,
            float_max=0.08,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="FAMAS | Spitfire",
            collection="The Dust 2 Collection", 
            rarity="Restricted",
            price=Decimal("12.30"),
            float_min=0.00,
            float_max=0.40,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Galil AR | Orange DDPAT",
            collection="The Dust 2 Collection",
            rarity="Mil-Spec",
            price=Decimal("1.85"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="M4A1-S | Bright Water",
            collection="The Dust 2 Collection",
            rarity="Mil-Spec", 
            price=Decimal("2.15"),
            float_min=0.00,
            float_max=0.40,
            marketable=True,
            stattrak=False
        ),
        
        # The Mirage Collection
        Skin(
            name="AK-47 | Emerald Pinstripe",
            collection="The Mirage Collection",
            rarity="Covert",
            price=Decimal("125.00"),
            float_min=0.00,
            float_max=0.40,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Desert Eagle | Pilot",
            collection="The Mirage Collection", 
            rarity="Classified",
            price=Decimal("28.90"),
            float_min=0.00,
            float_max=0.40,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="P250 | Bone Mask",
            collection="The Mirage Collection",
            rarity="Restricted",
            price=Decimal("3.25"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="MP9 | Hot Rod",
            collection="The Mirage Collection",
            rarity="Mil-Spec",
            price=Decimal("0.95"),
            float_min=0.00,
            float_max=0.08,
            marketable=True,
            stattrak=False
        ),
        
        # The Vertigo Collection  
        Skin(
            name="AK-47 | Redline",
            collection="The Vertigo Collection",
            rarity="Classified", 
            price=Decimal("42.00"),
            float_min=0.10,
            float_max=0.70,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="XM1014 | Scumbria",
            collection="The Vertigo Collection",
            rarity="Restricted",
            price=Decimal("5.80"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="P90 | Facility Negative",
            collection="The Vertigo Collection", 
            rarity="Mil-Spec",
            price=Decimal("1.20"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        
        # Add more cheap Mil-Spec skins for trade-up inputs
        Skin(
            name="MAC-10 | Silver",
            collection="The Dust 2 Collection",
            rarity="Mil-Spec",
            price=Decimal("0.45"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="UMP-45 | Urban DDPAT", 
            collection="The Dust 2 Collection",
            rarity="Mil-Spec",
            price=Decimal("0.38"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Nova | Predator",
            collection="The Mirage Collection",
            rarity="Mil-Spec",
            price=Decimal("0.52"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="MAG-7 | Silver",
            collection="The Mirage Collection", 
            rarity="Mil-Spec",
            price=Decimal("0.29"),
            float_min=0.05,
            float_max=0.60,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="MP7 | Olive Plaid",
            collection="The Vertigo Collection",
            rarity="Mil-Spec", 
            price=Decimal("0.67"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="Sawed-Off | Sage Spray",
            collection="The Vertigo Collection",
            rarity="Mil-Spec",
            price=Decimal("0.31"), 
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
        
        # Add more Restricted skins as trade-up targets
        Skin(
            name="AUG | Bengal Tiger",
            collection="The Dust 2 Collection",
            rarity="Restricted",
            price=Decimal("15.20"),
            float_min=0.00,
            float_max=1.00,
            marketable=True,
            stattrak=False
        ),
        Skin(
            name="SG 553 | Wave Spray",
            collection="The Mirage Collection",
            rarity="Restricted", 
            price=Decimal("4.75"),
            float_min=0.06,
            float_max=0.80,
            marketable=True,
            stattrak=False
        ),
    ]
    
    return mock_skins
