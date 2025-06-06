# filepath: c:\repos\CSTA\src\calculator.py
"""
Trade-up calculation engine implementing CS2 trade-up mechanics.
Handles probability calculations, profit analysis, and result generation.
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
from decimal import Decimal
from itertools import combinations_with_replacement
from dataclasses import dataclass

try:
    from .config import config
    from .models import (
        Skin, TradeUpInput, TradeUpResult, OutputSkin, 
        MarketData, CollectionInfo
    )
except ImportError:
    from config import config
    from models import (
        Skin, TradeUpInput, TradeUpResult, OutputSkin, 
        MarketData, CollectionInfo
    )

logger = logging.getLogger(__name__)

@dataclass
class TradeUpCandidate:
    """Represents a potential trade-up combination"""
    input_skins: List[Tuple[Skin, int]]  # (skin, quantity) pairs
    total_cost: Decimal
    expected_value: Decimal
    min_profit: Decimal
    max_profit: Decimal
    guaranteed_profit: Optional[Decimal]
    possible_outputs: List[OutputSkin]
    collections_used: Set[str]

class TradeUpCalculator:
    """Main trade-up calculation engine"""
    
    def __init__(self, market_data: MarketData):
        self.market_data = market_data
        self.rarity_mapping = config.trade_up.RARITY_MAPPING
    
    def find_profitable_tradeups(
        self, 
        min_profit: Decimal = Decimal('0'),
        max_input_price: Optional[Decimal] = None,
        target_collections: Optional[List[str]] = None
    ) -> List[TradeUpCandidate]:
        """
        Find all profitable trade-up opportunities
        
        Args:
            min_profit: Minimum profit threshold
            max_input_price: Maximum price per input skin
            target_collections: Specific collections to focus on
        
        Returns:
            List of profitable trade-up candidates sorted by profitability
        """
        logger.info("Starting profitable trade-up search...")
        candidates = []
        
        # Process each input rarity
        for input_rarity in self.rarity_mapping.keys():
            output_rarity = self.rarity_mapping[input_rarity]
            
            logger.info(f"Processing {input_rarity} -> {output_rarity} trade-ups")
            
            # Get available input skins
            input_skins = self._get_input_skins(
                input_rarity, max_input_price, target_collections
            )
            
            if len(input_skins) < 10:
                logger.warning(f"Not enough {input_rarity} skins for trade-ups")
                continue
            
            # Generate trade-up combinations
            trade_up_candidates = self._generate_trade_up_combinations(
                input_skins, output_rarity, min_profit
            )
            
            candidates.extend(trade_up_candidates)
        
        # Sort by profitability (guaranteed profit first, then expected value)
        candidates.sort(key=lambda c: (
            c.guaranteed_profit or Decimal('-999999'),
            c.expected_value
        ), reverse=True)
        
        logger.info(f"Found {len(candidates)} profitable trade-up opportunities")
        return candidates[:config.trade_up.MAX_RESULTS]
    
    def _get_input_skins(
        self, 
        rarity: str, 
        max_price: Optional[Decimal],
        target_collections: Optional[List[str]]
    ) -> List[Skin]:
        """Get available input skins for given rarity"""
        input_skins = []
        
        for collection_name, collection in self.market_data.collections.items():
            # Filter by target collections if specified
            if target_collections and collection_name not in target_collections:
                continue
                
            if rarity not in collection.skins_by_rarity:
                continue
            
            for skin in collection.skins_by_rarity[rarity]:
                # Filter by price if specified
                if max_price and skin.price > max_price:
                    continue
                    
                # Only include marketable skins
                if not skin.marketable:
                    continue
                    
                input_skins.append(skin)
        
        return input_skins
    
    def _generate_trade_up_combinations(
        self, 
        input_skins: List[Skin], 
        output_rarity: str,
        min_profit: Decimal
    ) -> List[TradeUpCandidate]:
        """Generate all viable trade-up combinations"""
        candidates = []
        
        # Group skins by collection for easier processing
        skins_by_collection = {}
        for skin in input_skins:
            if skin.collection not in skins_by_collection:
                skins_by_collection[skin.collection] = []
            skins_by_collection[skin.collection].append(skin)
        
        # Generate combinations using different collection mixes
        collections = list(skins_by_collection.keys())
        
        # Try different collection combinations (1-3 collections max for performance)
        for num_collections in range(1, min(4, len(collections) + 1)):
            for collection_combo in combinations_with_replacement(collections, num_collections):
                # Skip if too many of the same collection (limit variety)
                if collection_combo.count(collection_combo[0]) > 7:
                    continue
                
                candidate = self._evaluate_collection_combination(
                    collection_combo, skins_by_collection, output_rarity, min_profit
                )
                
                if candidate:
                    candidates.append(candidate)
        
        return candidates
    
    def _evaluate_collection_combination(
        self,
        collection_combo: Tuple[str, ...],
        skins_by_collection: Dict[str, List[Skin]],
        output_rarity: str,
        min_profit: Decimal
    ) -> Optional[TradeUpCandidate]:
        """Evaluate a specific collection combination"""
        
        # Get cheapest skins from each collection in the combo
        input_config = []
        total_cost = Decimal('0')
        collections_used = set()
        
        # Distribute 10 skins across the collections
        collection_counts = {}
        for collection in collection_combo:
            collection_counts[collection] = collection_counts.get(collection, 0) + 1
        
        # Ensure we have exactly 10 skins total
        total_allocated = sum(collection_counts.values())
        if total_allocated < 10:
            # Add remaining to the first collection
            first_collection = collection_combo[0]
            collection_counts[first_collection] += (10 - total_allocated)
        elif total_allocated > 10:
            # This shouldn't happen with our generation logic, but handle it
            return None
        
        # Select cheapest skins from each collection
        for collection, count in collection_counts.items():
            available_skins = skins_by_collection[collection]
            if len(available_skins) < count:
                return None  # Not enough skins in this collection
            
            # Take the cheapest skins
            cheapest_skins = sorted(available_skins, key=lambda s: s.price)[:count]
            
            for skin in cheapest_skins:
                input_config.append((skin, 1))
                total_cost += skin.price
                collections_used.add(collection)
        
        # Calculate possible outputs
        possible_outputs = self._calculate_outputs(collections_used, output_rarity)
        if not possible_outputs:
            return None
        
        # Calculate probabilities and values
        expected_value, min_profit_val, max_profit_val, guaranteed_profit = \
            self._calculate_trade_up_value(input_config, possible_outputs, total_cost)
        
        # Filter by minimum profit requirement
        if expected_value < min_profit and (not guaranteed_profit or guaranteed_profit < min_profit):
            return None
        
        return TradeUpCandidate(
            input_skins=input_config,
            total_cost=total_cost,
            expected_value=expected_value,
            min_profit=min_profit_val,
            max_profit=max_profit_val,
            guaranteed_profit=guaranteed_profit,
            possible_outputs=possible_outputs,
            collections_used=collections_used
        )
    
    def _calculate_outputs(self, input_collections: Set[str], output_rarity: str) -> List[OutputSkin]:
        """Calculate possible output skins and their probabilities"""
        possible_outputs = []
        total_weight = 0
        
        # For each input collection, find output skins of target rarity
        for collection_name in input_collections:
            if collection_name not in self.market_data.collections:
                continue
                
            collection = self.market_data.collections[collection_name]
            if output_rarity not in collection.skins_by_rarity:
                continue
            
            # Count skins in this collection (weight = k_C)
            collection_weight = len(collection.skins_by_rarity[output_rarity])
            total_weight += collection_weight
            
            # Add each skin as possible output            
            for skin in collection.skins_by_rarity[output_rarity]:
                # Skip non-marketable skins
                if not skin.marketable:
                    continue
                    
                possible_outputs.append(OutputSkin(
                    skin=skin,
                    probability=Decimal('0')  # Will be calculated below
                ))
        
        # Calculate actual probabilities using k_C / total_weight formula
        if total_weight == 0:
            return []
        
        # Group outputs by collection and calculate probabilities
        outputs_by_collection = {}
        for output in possible_outputs:
            collection = output.skin.collection
            if collection not in outputs_by_collection:
                outputs_by_collection[collection] = []
            outputs_by_collection[collection].append(output)
        
        # Set probabilities: each skin gets (1/k_C) * (k_C/total_weight) = 1/total_weight
        for collection_name, collection_outputs in outputs_by_collection.items():
            collection_weight = len(collection_outputs)
            collection_probability = Decimal(collection_weight) / Decimal(total_weight)
            skin_probability = collection_probability / Decimal(collection_weight)
            
            for output in collection_outputs:
                output.probability = skin_probability
        
        return possible_outputs
    
    def _calculate_trade_up_value(
        self, 
        input_config: List[Tuple[Skin, int]], 
        possible_outputs: List[OutputSkin],
        total_cost: Decimal
    ) -> Tuple[Decimal, Decimal, Decimal, Optional[Decimal]]:
        """
        Calculate trade-up values
        
        Returns:
            (expected_value, min_profit, max_profit, guaranteed_profit)
        """
        if not possible_outputs:
            return Decimal('0'), Decimal('0'), Decimal('0'), None
        
        # Calculate expected value
        expected_output_value = sum(
            output.skin.price * output.probability 
            for output in possible_outputs
        )
        expected_profit = expected_output_value - total_cost
        
        # Calculate min/max profits
        output_prices = [output.skin.price for output in possible_outputs]
        min_output_price = min(output_prices)
        max_output_price = max(output_prices)
        
        min_profit = min_output_price - total_cost
        max_profit = max_output_price - total_cost
        
        # Check for guaranteed profit (all outputs profitable)
        guaranteed_profit = None
        if min_profit > 0:
            guaranteed_profit = min_profit
        
        return expected_profit, min_profit, max_profit, guaranteed_profit
    
    def calculate_detailed_result(self, candidate: TradeUpCandidate) -> TradeUpResult:
        """Convert candidate to detailed TradeUpResult"""
          # Create input object
        input_skins_list = []
        for skin, quantity in candidate.input_skins:
            for _ in range(quantity):
                input_skins_list.append(skin)
        
        # Calculate collection information
        collections = list(candidate.collections_used)
        collection1 = collections[0] if collections else "unknown"
        collection2 = collections[1] if len(collections) > 1 else None
        
        # Calculate split ratio (count of skins from each collection)
        collection_counts = {}
        for skin in input_skins_list:
            collection_counts[skin.collection] = collection_counts.get(skin.collection, 0) + 1
        
        if collection2:
            split_ratio = (collection_counts.get(collection1, 0), collection_counts.get(collection2, 0))
        else:
            split_ratio = (collection_counts.get(collection1, 0), 0)
        
        # Calculate average float
        total_float = sum(skin.float_mid for skin in input_skins_list)
        average_float = total_float / len(input_skins_list) if input_skins_list else 0.0
        
        trade_input = TradeUpInput(
            collection1=collection1,
            collection2=collection2,
            split_ratio=split_ratio,
            skins=input_skins_list,
            total_cost=candidate.total_cost,
            average_float=average_float
        )
        
        # Sort outputs by probability (highest first)
        sorted_outputs = sorted(
            candidate.possible_outputs, 
            key=lambda o: o.probability, 
            reverse=True
        )
        
        return TradeUpResult(
            input_config=trade_input,
            output_skins=sorted_outputs,
            expected_output_price=candidate.expected_value,
            raw_profit=candidate.expected_value - candidate.total_cost,
            roi_percentage=float((candidate.expected_value - candidate.total_cost) / candidate.total_cost * 100),
            guaranteed_profit=candidate.guaranteed_profit is not None,
            min_output_price=min(output.skin.price for output in candidate.possible_outputs) if candidate.possible_outputs else Decimal('0')
        )

def create_calculator(market_data: MarketData) -> TradeUpCalculator:
    """Factory function to create calculator instance"""
    return TradeUpCalculator(market_data)