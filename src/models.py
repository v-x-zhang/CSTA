"""
Data models for CS2 Trade-up Calculator
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from decimal import Decimal

@dataclass
class Skin:
    """Represents a CS2 skin with all necessary information"""
    name: str
    collection: str
    rarity: str
    price: Decimal
    float_min: float
    float_max: float
    marketable: bool = True
    stattrak: bool = False
    
    @property
    def float_mid(self) -> float:
        """Midpoint of float range for calculations"""
        return (self.float_min + self.float_max) / 2
    
    def __str__(self) -> str:
        return f"{self.name} ({self.collection}) - ${self.price}"

@dataclass
class TradeUpInput:
    """Represents a single trade-up input configuration"""
    collection1: str
    collection2: Optional[str]
    split_ratio: Tuple[int, int]  # (collection1_count, collection2_count)
    skins: List[Skin]
    total_cost: Decimal
    average_float: float

@dataclass 
class OutputSkin:
    """Represents a possible output skin with probability"""
    skin: Skin
    probability: float
    
    @property
    def expected_value(self) -> Decimal:
        """Expected value contribution of this skin"""
        return self.skin.price * Decimal(str(self.probability))

@dataclass
class TradeUpResult:
    """Complete trade-up analysis result"""
    input_config: TradeUpInput
    output_skins: List[OutputSkin]
    expected_output_price: Decimal
    raw_profit: Decimal
    roi_percentage: float
    guaranteed_profit: bool
    min_output_price: Decimal
    
    @property
    def is_profitable(self) -> bool:
        """Whether this trade-up has positive expected value"""
        return self.raw_profit > 0
    
    @property
    def expected_profit(self) -> Decimal:
        """Expected profit - alias for raw_profit for compatibility"""
        return self.raw_profit
    
    @property
    def profit_margin(self) -> Decimal:
        """Absolute profit margin for guaranteed profits"""
        if self.guaranteed_profit:
            return self.min_output_price - self.input_config.total_cost
        return Decimal('0')

@dataclass
class CollectionInfo:
    """Information about a skin collection and its rarities"""
    name: str
    skins_by_rarity: Dict[str, List[Skin]]
    
    def get_skins(self, rarity: str) -> List[Skin]:
        """Get all skins of a specific rarity in this collection"""
        return self.skins_by_rarity.get(rarity, [])
    
    def has_rarity(self, rarity: str) -> bool:
        """Check if collection has skins of specific rarity"""
        return rarity in self.skins_by_rarity and len(self.skins_by_rarity[rarity]) > 0

@dataclass
class MarketData:
    """Container for all market data organized by collection and rarity"""
    collections: Dict[str, CollectionInfo]
    last_updated: float  # timestamp
    
    def get_collection(self, name: str) -> Optional[CollectionInfo]:
        """Get collection by name"""
        return self.collections.get(name)
    
    def get_collections_with_rarity(self, rarity: str) -> List[str]:
        """Get all collection names that have skins of specified rarity"""
        return [name for name, collection in self.collections.items() 
                if collection.has_rarity(rarity)]
    
    def get_tradeable_collections(self, from_rarity: str, to_rarity: str) -> List[str]:
        """Get collections that can trade up from one rarity to another"""
        return [name for name, collection in self.collections.items()
                if collection.has_rarity(from_rarity) and collection.has_rarity(to_rarity)]
