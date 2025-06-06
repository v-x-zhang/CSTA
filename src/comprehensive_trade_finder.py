"""
Comprehensive Trade-up Finder for CS2
Uses comprehensive database for skin metadata + runtime pricing for calculations
"""

import asyncio
import logging
import aiohttp
from typing import List, Optional, Dict, Tuple
from decimal import Decimal
from collections import defaultdict, Counter

try:
    from .comprehensive_database import ComprehensiveDatabaseManager
    from .runtime_pricing import RuntimePricingClient
    from .calculator import TradeUpCalculator, TradeUpCandidate
    from .models import MarketData, TradeUpResult, Skin, TradeUpInput, OutputSkin
    from .csfloat_listings import CSFloatListingsClient
    # from .cache_manager import CacheManager  # Temporarily disabled
except ImportError:
    # Fallback for direct execution
    from comprehensive_database import ComprehensiveDatabaseManager
    from runtime_pricing import RuntimePricingClient
    from calculator import TradeUpCalculator, TradeUpCandidate
    from models import MarketData, TradeUpResult, Skin, TradeUpInput, OutputSkin
    from csfloat_listings import CSFloatListingsClient
    # from cache_manager import CacheManager  # Temporarily disabled

logger = logging.getLogger(__name__)

class ComprehensiveTradeUpFinder:
    """Trade-up finder using comprehensive database + runtime pricing"""
    
    def __init__(self, use_steam_pricing: bool = False):
        self.db_manager = ComprehensiveDatabaseManager()
        self.use_steam_pricing = use_steam_pricing
        
        if use_steam_pricing:
            from .steam_pricing import SteamPricingClient
            self.pricing_client = SteamPricingClient()
            logger.info("Using Steam Market pricing as data source")
        else:
            self.pricing_client = RuntimePricingClient()
            logger.info("Using external API pricing as data source")
        
        self.csfloat_client = CSFloatListingsClient()
        self.calculator = None
        self.market_data = None
        self._cached_prices = {}

    async def initialize(self, sample_size: int = None, use_all_prices: bool = False) -> None:
        """Initialize with pricing data
        
        Args:
            sample_size: Number of prices to load (ignored if use_all_prices=True)
            use_all_prices: If True, load all available pricing data instead of limiting
        """
        logger.info("Initializing Comprehensive Trade-up Finder...")
        
        if use_all_prices:
            # Load all available prices
            logger.info("Loading ALL available pricing data...")
            all_prices = await self.pricing_client.get_all_prices()
            self._cached_prices.update(all_prices)
            logger.info(f"Loaded {len(all_prices)} prices from complete dataset")
        else:
            # Use sample size (default behavior for backward compatibility)
            if sample_size is None:
                sample_size = 1000
            logger.info(f"Fetching sample prices (limit: {sample_size})...")
            sample_prices = await self.pricing_client.get_sample_prices(limit=sample_size)
            self._cached_prices.update(sample_prices)
            logger.info(f"Loaded {len(sample_prices)} sample prices")
        
        # Build market data using comprehensive database + pricing data
        self.market_data = self.db_manager.build_market_data_from_comprehensive(self._cached_prices)
        
        # Initialize calculator
        self.calculator = TradeUpCalculator(self.market_data)
        
        logger.info(f"Initialized with {len(self.market_data.collections)} collections and {len(self._cached_prices)} prices")
    
    async def find_profitable_trades(self,
                                   min_profit: float = 1.0,
                                   max_input_price: Optional[float] = None,
                                   target_collections: Optional[List[str]] = None,
                                   limit: int = 10,
                                   offset: int = 0
                                   ) -> List[TradeUpResult]:
        """Find profitable trade-up opportunities following CS:GO trade-up rules"""
        logger.info(f"Searching for profitable trades (min_profit: ${min_profit}, offset: {offset})...")

        opportunities = []

        # Get all trade-able rarities
        rarities_to_check = ['Consumer Grade', 'Industrial Grade', 'Mil-Spec Grade', 'Restricted', 'Classified']

        skipped = 0  # Track how many trade-ups have been skipped

        for input_rarity in rarities_to_check:
            logger.info(f"Checking {input_rarity} trade-ups...")

            # Get collections that have this rarity
            collections = self.db_manager.get_collections_by_rarity(input_rarity)

            # Filter to target collections if specified
            if target_collections:
                collections = [c for c in collections if c in target_collections]

            # Try different input collection combinations
            for primary_collection in collections:
                primary_input_skins = self.db_manager.get_skins_by_collection_and_rarity(primary_collection, input_rarity)
                if not primary_input_skins:
                    continue

                # Single collection trade-ups
                if len(primary_input_skins) >= 1:
                    try:
                        result = await self._calculate_single_collection_tradeup(
                            primary_collection, input_rarity, primary_input_skins,
                            max_input_price, min_profit
                        )
                        if result:
                            if skipped < offset:
                                skipped += 1
                                continue
                            opportunities.append(result)
                            if len(opportunities) >= limit:
                                opportunities.sort(key=lambda x: x.expected_profit, reverse=True)
                                return opportunities[:limit]
                    except Exception as e:
                        logger.debug(f"Error in single collection trade-up: {e}")

                # Mixed collection trade-ups
                for secondary_collection in collections:
                    if secondary_collection <= primary_collection:
                        continue

                    secondary_input_skins = self.db_manager.get_skins_by_collection_and_rarity(secondary_collection, input_rarity)
                    if not secondary_input_skins:
                        continue

                    for split in [(9, 1), (8, 2), (7, 3), (6, 4), (5, 5)]:
                        try:
                            result = await self._calculate_mixed_collection_tradeup(
                                primary_collection, secondary_collection, input_rarity,
                                primary_input_skins, secondary_input_skins, split,
                                max_input_price, min_profit
                            )
                            if result:
                                if skipped < offset:
                                    skipped += 1
                                    continue
                                opportunities.append(result)
                                if len(opportunities) >= limit:
                                    opportunities.sort(key=lambda x: x.expected_profit, reverse=True)
                                    return opportunities[:limit]
                        except Exception as e:
                            logger.debug(f"Error in mixed collection trade-up: {e}")

        opportunities.sort(key=lambda x: x.expected_profit, reverse=True)
        return opportunities[:limit]
    
    async def _calculate_single_collection_tradeup(self,
                                                  collection: str,
                                                  input_rarity: str,
                                                  input_skins: List[Dict],
                                                  max_input_price: Optional[float],
                                                  min_profit: float) -> Optional[TradeUpResult]:
        """Calculate trade-up using 10 items from a single collection"""
        
        # Get output rarity
        rarity_progression = {
            'Consumer Grade': 'Industrial Grade',
            'Industrial Grade': 'Mil-Spec Grade',
            'Mil-Spec Grade': 'Restricted',
            'Restricted': 'Classified',
            'Classified': 'Covert'
        }
        
        output_rarity = rarity_progression.get(input_rarity)
        if not output_rarity:
            return None
          # Filter input skins to only marketable ones
        marketable_inputs = [skin for skin in input_skins if self._is_marketable_skin(skin)]
        if not marketable_inputs:
            return None
          # Get possible outputs from the same collection (no souvenirs)
        all_output_skins = self.db_manager.get_skins_by_collection_and_rarity(collection, output_rarity)
        marketable_outputs = [skin for skin in all_output_skins if self._is_marketable_skin(skin)]
        if not marketable_outputs:
            return None
        
        # Deduplicate output skins by base name (remove condition duplicates)
        # Keep only one entry per base skin name
        unique_base_outputs = {}
        for skin in marketable_outputs:
            base_name = self._extract_base_skin_name(skin['market_hash_name'])
            if base_name not in unique_base_outputs:
                unique_base_outputs[base_name] = skin
        
        marketable_outputs = list(unique_base_outputs.values())
          # Get pricing data for inputs and outputs
        input_names = [skin['market_hash_name'] for skin in marketable_inputs]
        output_names = [skin['market_hash_name'] for skin in marketable_outputs]
        all_names = list(set(input_names + output_names))
        missing_prices = [name for name in all_names if name not in self._cached_prices]
        if missing_prices:
            new_prices = await self.pricing_client.fetch_prices_for_items(missing_prices)
            
            if self.use_steam_pricing:
                # When using Steam pricing, skip validation since Steam API is authoritative
                self._cached_prices.update(new_prices)
                logger.debug(f"Using Steam pricing directly for {len(new_prices)} items (no validation needed)")
            else:
                # Validate and correct suspicious prices using Steam as reference
                validated_prices = await self._validate_prices(new_prices, marketable_inputs + marketable_outputs)
                self._cached_prices.update(validated_prices)
        
        # Find best input skin for different wear conditions
        best_result = None
        best_profit = min_profit
        for condition in ['Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred']:
            condition_inputs = [s for s in marketable_inputs if s.get('condition_name') == condition]
            if not condition_inputs:
                continue
            # Find cheapest input in this condition
            cheapest_input = None
            cheapest_price = float('inf')            
            for skin in condition_inputs:
                price = self._cached_prices.get(skin['market_hash_name'])
                if price and (not max_input_price or float(price) <= max_input_price):
                    if self.use_steam_pricing:
                        # When using Steam pricing, bypass validation checks since Steam is authoritative
                        final_price = float(price)
                    else:
                        # Check price validation status - only include validated prices
                        validation_status = self.db_manager.get_price_validation_status(skin['market_hash_name'])
                        if validation_status and validation_status.get('status') == 'invalid':
                            continue  # Skip skins marked as invalid
                        # Include valid and unvalidated skins (unvalidated will be validated later)
                        
                        # Use Steam-validated price if available, otherwise external price
                        final_price = float(price)
                        if validation_status and validation_status.get('status') == 'valid':
                            steam_price = validation_status.get('steam_price')
                            if steam_price and steam_price > 0:
                                final_price = float(steam_price)
                    
                    if final_price < cheapest_price:
                        cheapest_input = skin
                        cheapest_price = final_price
            
            if not cheapest_input:
                continue
            
            total_input_cost = cheapest_price * 10
              # Calculate deterministic output float
            input_float = self._get_condition_float(cheapest_input)
            
            # All outputs are now possible since we scale the float to each output's range
            valid_outputs = marketable_outputs            # Calculate expected output value using proper trade-up probabilities
            # For single collection: all outputs have equal probability (1/m_C)
            # Only include outputs with valid pricing data AND valid price validation status
            valid_priced_outputs = []
            for output_skin in valid_outputs:
                # Calculate the actual output float and condition after scaling
                scaled_float, predicted_condition = self._calculate_output_float_and_condition(input_float, output_skin, cheapest_input)
                
                # Look for condition-specific pricing first
                condition_market_name = f"{output_skin['market_hash_name']} ({predicted_condition})"
                base_market_name = output_skin['market_hash_name']
                
                # Try to get price for the specific condition first, then fallback to base name
                output_price = self._cached_prices.get(condition_market_name)
                if not output_price:
                    output_price = self._cached_prices.get(base_market_name)
                if output_price and float(output_price) > 0:  # Check if we have price data
                    if self.use_steam_pricing:
                        # When using Steam pricing, bypass validation checks since Steam is authoritative
                        valid_priced_outputs.append((output_skin, float(output_price), scaled_float, predicted_condition))
                    else:
                        # Check price validation status - only include validated prices
                        validation_status = self.db_manager.get_price_validation_status(base_market_name)
                        if validation_status and validation_status.get('status') == 'valid':
                            # Use Steam-validated price instead of external API price
                            steam_price = validation_status.get('steam_price')
                            if steam_price and steam_price > 0:
                                valid_priced_outputs.append((output_skin, float(steam_price), scaled_float, predicted_condition))
                            else:
                                # Fallback to external price if Steam price is missing
                                valid_priced_outputs.append((output_skin, float(output_price), scaled_float, predicted_condition))
                        # If no validation status yet, include for now (will be validated later)
                        elif validation_status is None or validation_status.get('status') == 'unvalidated':
                            valid_priced_outputs.append((output_skin, float(output_price), scaled_float, predicted_condition))
            if not valid_priced_outputs:
                continue  # Skip if no valid pricing data
            
            num_outputs = len(valid_priced_outputs)
            expected_output_value = 0
            
            output_skin_objects = []            
            for output_skin, output_price, scaled_float, predicted_condition in valid_priced_outputs:
                # Equal probability for each output in single collection
                probability = 1.0 / num_outputs
                expected_output_value += output_price * probability                
                skin_obj = Skin(
                    name=f"{output_skin['market_hash_name']} ({predicted_condition})",
                    rarity=output_skin['rarity'],
                    price=Decimal(str(output_price)),
                    collection=collection,
                    float_min=output_skin.get('min_float', 0.0),
                    float_max=output_skin.get('max_float', 1.0)
                )
                output_obj = OutputSkin(skin=skin_obj, probability=probability)
                # Store predicted condition for display
                output_obj.predicted_condition = predicted_condition
                output_obj.predicted_float = scaled_float
                output_skin_objects.append(output_obj)
            
            # Apply Steam market fee (15%)
            expected_output_value *= 0.85
            expected_profit = expected_output_value - total_input_cost
            
            if expected_profit > best_profit:
                best_profit = expected_profit
                
                # Create input configuration
                input_skin = Skin(
                    name=cheapest_input['market_hash_name'],
                    rarity=cheapest_input['rarity'],
                    price=Decimal(str(cheapest_price)),
                    collection=collection,
                    float_min=cheapest_input.get('min_float', 0.0),
                    float_max=cheapest_input.get('max_float', 1.0)
                )
                
                trade_input = TradeUpInput(
                    collection1=collection,
                    collection2=None,
                    split_ratio=(10, 0),
                    skins=[input_skin] * 10,
                    total_cost=Decimal(str(total_input_cost)),
                    average_float=input_float
                )
                
                best_result = TradeUpResult(
                    input_config=trade_input,
                    output_skins=output_skin_objects,
                    expected_output_price=Decimal(str(expected_output_value)),
                    raw_profit=Decimal(str(expected_profit)),
                    roi_percentage=float(expected_profit / total_input_cost * 100),
                    guaranteed_profit=False,
                    min_output_price=min(Decimal(str(price)) for _, price, _, _ in valid_priced_outputs)
                )
        
        return best_result
        """Calculate a specific trade-up opportunity"""
        
        # Get item names for pricing
        input_names = [skin['market_hash_name'] for skin in input_skins]
        output_names = [skin['market_hash_name'] for skin in output_skins]
        all_names = list(set(input_names + output_names))
        
        # Fetch prices for items we don't have cached
        missing_prices = [name for name in all_names if name not in self._cached_prices]
        if missing_prices:
            new_prices = await self.pricing_client.fetch_prices_for_items(missing_prices)
            self._cached_prices.update(new_prices)
        
        # Find cheapest inputs for each wear condition
        input_candidates = []
        for condition in ['Factory New', 'Minimal Wear', 'Field-Tested', 'Well-Worn', 'Battle-Scarred']:
            condition_inputs = [s for s in input_skins if s.get('condition_name') == condition]
            if not condition_inputs:
                continue
                
            # Get prices and find cheapest
            cheapest = None
            cheapest_price = float('inf')
            
            for skin in condition_inputs:
                price = self._cached_prices.get(skin['market_hash_name'])
                if price and (not max_input_price or float(price) <= max_input_price):
                    if float(price) < cheapest_price:
                        cheapest = skin
                        cheapest_price = float(price)
            
            if cheapest:
                input_candidates.append({
                    'skin': cheapest,
                    'price': cheapest_price,
                    'condition': condition
                })
        
        if not input_candidates:
            return None
        
        # Calculate expected outputs and profits for each input condition
        best_result = None
        best_profit = 0
        
        for input_candidate in input_candidates:
            input_condition = input_candidate['condition']
            input_price = input_candidate['price']
            total_input_cost = input_price * 10  # Need 10 items
            
            # Calculate expected output value
            expected_output_value = 0
            total_probability = 0
            
            for output_skin in output_skins:
                # Get price for this output
                output_price = self._cached_prices.get(output_skin['market_hash_name'])
                if not output_price:
                    continue
                
                # Calculate probability (simplified - assume equal probability for now)
                probability = 1.0 / len(output_skins)
                expected_output_value += float(output_price) * probability
                total_probability += probability
            
            if total_probability == 0:
                continue
              # Steam market fee (15%)
            expected_output_value *= 0.85
            
            expected_profit = expected_output_value - total_input_cost
            
            if expected_profit > min_profit and expected_profit > best_profit:
                best_profit = expected_profit                # Create input configuration
                input_skin = Skin(
                    name=input_candidate['skin']['market_hash_name'],
                    rarity=input_candidate['skin']['rarity'],
                    price=Decimal(str(input_price)),
                    collection=input_collection,
                    float_min=input_candidate['skin'].get('min_float', 0.0),
                    float_max=input_candidate['skin'].get('max_float', 1.0)
                )
                
                trade_input = TradeUpInput(
                    collection1=input_collection,
                    collection2=None,
                    split_ratio=(10, 0),  # All from one collection
                    skins=[input_skin] * 10,  # 10 copies of the cheapest input
                    total_cost=Decimal(str(total_input_cost)),
                    average_float=input_skin.float_mid
                )
                  # Create output skins
                output_skin_objects = []
                for output_skin in output_skins:
                    skin_obj = Skin(
                        name=output_skin['market_hash_name'],
                        rarity=output_skin['rarity'],
                        price=Decimal(str(output_skin.get('price', 0))),
                        collection=output_collection,
                        float_min=output_skin.get('min_float', 0.0),
                        float_max=output_skin.get('max_float', 1.0)
                    )
                    probability = 1.0 / len(output_skins)  # Equal probability for each output
                    output_skin_objects.append(OutputSkin(skin=skin_obj, probability=probability))
                
                # Create result
                best_result = TradeUpResult(
                    input_config=trade_input,
                    output_skins=output_skin_objects,
                    expected_output_price=Decimal(str(expected_output_value)),
                    raw_profit=Decimal(str(expected_profit)),
                    roi_percentage=float(expected_profit / total_input_cost * 100),
                    guaranteed_profit=True,  # This is from the guaranteed method
                    min_output_price=min(Decimal(str(output_skin.get('price', 0))) for output_skin in output_skins)
                )
        
        return best_result
    
    async def find_guaranteed_profit_trades(self,
                                          max_input_price: Optional[float] = None,
                                          target_collections: Optional[List[str]] = None,
                                          limit: int = 10) -> List[TradeUpResult]:
        """Find guaranteed profit trade-ups (cheapest output > total input cost)"""
        logger.info("Searching for guaranteed profit trades...")
        
        # For guaranteed profits, we need to find cases where the cheapest possible output
        # is worth more than the total input cost
        opportunities = []
        
        rarities_to_check = ['Consumer Grade', 'Industrial Grade', 'Mil-Spec Grade', 'Restricted', 'Classified']
        
        for input_rarity in rarities_to_check:
            possible_outputs = self.db_manager.get_possible_outputs(input_rarity)
            if not possible_outputs:
                continue
                
            collections = self.db_manager.get_collections_by_rarity(input_rarity)
            if target_collections:
                collections = [c for c in collections if c in target_collections]
            
            for collection in collections:
                input_skins = self.db_manager.get_skins_by_collection_and_rarity(collection, input_rarity)
                if len(input_skins) < 10:
                    continue
                
                try:
                    result = await self._find_guaranteed_profit_for_collection(
                        input_skins, possible_outputs, collection, max_input_price
                    )
                    if result:
                        opportunities.append(result)
                except Exception as e:
                    logger.debug(f"Error in guaranteed profit calculation: {e}")
                    continue
        
        opportunities.sort(key=lambda x: x.expected_profit, reverse=True)
        return opportunities[:limit]
    
    async def _find_guaranteed_profit_for_collection(self,
                                                   input_skins: List[Dict],
                                                   output_skins: List[Dict],
                                                   collection: str,
                                                   max_input_price: Optional[float]) -> Optional[TradeUpResult]:
        """Find guaranteed profit for a specific collection"""
        
        # Get pricing data
        input_names = [skin['market_hash_name'] for skin in input_skins]
        output_names = [skin['market_hash_name'] for skin in output_skins]
        all_names = list(set(input_names + output_names))
        
        missing_prices = [name for name in all_names if name not in self._cached_prices]
        if missing_prices:
            new_prices = await self.pricing_client.fetch_prices_for_items(missing_prices)
            self._cached_prices.update(new_prices)
        
        # Find cheapest input
        cheapest_input_price = float('inf')
        cheapest_input = None
        
        for skin in input_skins:
            price = self._cached_prices.get(skin['market_hash_name'])
            if price and (not max_input_price or float(price) <= max_input_price):
                if float(price) < cheapest_input_price:
                    cheapest_input_price = float(price)
                    cheapest_input = skin
        
        if not cheapest_input:
            return None
        
        total_input_cost = cheapest_input_price * 10
        
        # Find cheapest output
        cheapest_output_price = float('inf')        
        for output in output_skins:
            price = self._cached_prices.get(output['market_hash_name'])
            if price and float(price) < cheapest_output_price:
                cheapest_output_price = float(price)
        
        if cheapest_output_price == float('inf'):
            return None
        
        # Apply market fees
        net_output_value = cheapest_output_price * 0.85        
        profit = net_output_value - total_input_cost
        
        if profit > 0:
            # Create input configuration
            input_skin = Skin(
                name=cheapest_input['market_hash_name'],
                rarity=cheapest_input['rarity'],
                price=Decimal(str(cheapest_input_price)),
                collection=collection,
                float_min=cheapest_input.get('min_float', 0.0),
                float_max=cheapest_input.get('max_float', 1.0)
            )
            
            trade_input = TradeUpInput(
                collection1=collection,
                collection2=None,                split_ratio=(10, 0),  # All from one collection
                skins=[input_skin] * 10,  # 10 copies of the cheapest input
                total_cost=Decimal(str(total_input_cost)),
                average_float=input_skin.float_mid
            )
            
            # Create output skins
            output_skin_objects = []
            for output_skin in output_skins:
                skin_obj = Skin(
                    name=output_skin['market_hash_name'],
                    rarity=output_skin['rarity'],
                    price=Decimal(str(output_skin.get('price', 0))),
                    collection="Mixed",  # Could be multiple collections
                    float_min=output_skin.get('min_float', 0.0),
                    float_max=output_skin.get('max_float', 1.0)
                )
                probability = 1.0 / len(output_skins)  # Equal probability for each output
                output_skin_objects.append(OutputSkin(skin=skin_obj, probability=probability))
            
            return TradeUpResult(
                input_config=trade_input,
                output_skins=output_skin_objects,
                expected_output_price=Decimal(str(net_output_value)),
                raw_profit=Decimal(str(profit)),
                roi_percentage=float(profit / total_input_cost * 100),
                guaranteed_profit=True,  # This is from the guaranteed method
                min_output_price=min(Decimal(str(output_skin.get('price', 0))) for output_skin in output_skins)
            )
        
        return None
    async def find_positive_return_with_csfloat_validation(self,
                                                          selling_fee_rate: float = 0.15,
                                                          target_collections: Optional[List[str]] = None) -> Optional[Dict]:
        """
        Find the first trade-up with positive expected return (after selling fees)
        and validate with actual CSFloat listings and float values
        """
        logger.info("Searching for positive expected return trade-ups with CSFloat validation...")
        
        # Get all trade-able rarities
        rarities_to_check = ['Consumer Grade', 'Industrial Grade', 'Mil-Spec Grade', 'Restricted', 'Classified']
        
        async with aiohttp.ClientSession() as session:
            for input_rarity in rarities_to_check:
                logger.info(f"Checking {input_rarity} trade-ups...")
                
                # Get collections that have this rarity
                collections = self.db_manager.get_collections_by_rarity(input_rarity)
                
                # Filter to target collections if specified
                if target_collections:
                    collections = [c for c in collections if c in target_collections]
                
                for collection in collections:
                    # Get input skins from this collection/rarity
                    input_skins = self.db_manager.get_skins_by_collection_and_rarity(collection, input_rarity)
                    if not input_skins:
                        continue
                    
                    logger.debug(f"Checking collection: {collection} with {len(input_skins)} input skins")
                    
                    # Try to find a positive return trade-up for this collection
                    result = await self._calculate_csfloat_validated_tradeup(
                        collection, input_rarity, input_skins, selling_fee_rate, session
                    )
                    
                    if result:
                        logger.info(f"Found positive return trade-up in {collection}!")
                        return result
        
        logger.info("No positive expected return trade-ups found")
        return None
    
    async def _calculate_csfloat_validated_tradeup(self,
                                                  collection: str,
                                                  input_rarity: str,
                                                  input_skins: List[Dict],
                                                  selling_fee_rate: float,
                                                  session: aiohttp.ClientSession) -> Optional[Dict]:
        """Calculate and validate a trade-up using CSFloat real-time data"""
        
        # Get output rarity and possible outputs
        rarity_progression = {
            'Consumer Grade': 'Industrial Grade',
            'Industrial Grade': 'Mil-Spec Grade',
            'Mil-Spec Grade': 'Restricted',
            'Restricted': 'Classified',
            'Classified': 'Covert'
        }
        
        output_rarity = rarity_progression.get(input_rarity)
        if not output_rarity:
            return None
        
        # Get possible outputs from the same collection
        output_skins = self.db_manager.get_skins_by_collection_and_rarity(collection, output_rarity)
        if not output_skins:
            return None
        
        # Find the cheapest input skin that we can buy 10 of
        cheapest_input = None
        for skin in input_skins:
            if self._has_price(skin['market_hash_name']):
                if not cheapest_input or self._get_price(skin['market_hash_name']) < self._get_price(cheapest_input['market_hash_name']):
                    cheapest_input = skin
        
        if not cheapest_input:
            return None
        
        # Calculate basic expected value first to see if it's worth CSFloat validation
        input_cost = self._get_price(cheapest_input['market_hash_name']) * 10
        
        # Quick expected value calculation
        total_expected_value = 0
        total_probability = 0
        
        for output_skin in output_skins:
            if self._has_price(output_skin['market_hash_name']):
                price = self._get_price(output_skin['market_hash_name'])
                # All outputs have equal probability (1/number_of_outputs)
                probability = 1.0 / len(output_skins)
                total_expected_value += price * probability
                total_probability += probability
        
        if total_probability == 0:
            return None
        
        # Apply selling fee
        net_expected_value = total_expected_value * (1 - selling_fee_rate)
        expected_profit = net_expected_value - input_cost
        
        logger.debug(f"Basic calculation: Cost=${input_cost:.2f}, Expected=${net_expected_value:.2f}, Profit=${expected_profit:.2f}")
        
        # Only proceed with CSFloat validation if we have positive expected return
        if expected_profit <= 0:
            return None
        
        logger.info(f"Positive expected return found! Validating with CSFloat...")
        
        # Now get actual CSFloat listings for input and output skins
        input_skin_name = cheapest_input['market_hash_name']
        input_listings = await self.csfloat_client.get_listings_for_skin(input_skin_name, session, limit=10)
        
        if len(input_listings) < 10:
            logger.warning(f"Not enough CSFloat listings for {input_skin_name}. Found {len(input_listings)}, need 10")
            return None
        
        # Get actual purchase info for 10 input items
        input_purchase_info = self.csfloat_client.get_purchase_info(input_listings, 10)
        if not input_purchase_info['available']:
            logger.warning(f"Cannot purchase 10x {input_skin_name} from CSFloat")
            return None
        
        # Get CSFloat listings for all possible outputs
        output_listings_data = {}
        for output_skin in output_skins:
            output_name = output_skin['market_hash_name']
            listings = await self.csfloat_client.get_listings_for_skin(output_name, session, limit=5)
            if listings:
                output_listings_data[output_name] = {
                    'skin_data': output_skin,
                    'listings': listings,
                    'average_price': sum(l['price'] for l in listings) / len(listings)
                }
        if not output_listings_data:
            logger.warning("No CSFloat listings found for any output skins")
            return None
          # Calculate actual float values and probabilities
        input_floats = [listing['float'] for listing in input_purchase_info['purchase_plan']]
        average_input_float = sum(input_floats) / len(input_floats)
        
        # Calculate expected output values with actual CSFloat prices
        total_csfloat_expected_value = 0
        output_details = []
        
        for output_name, output_data in output_listings_data.items():
            output_skin = output_data['skin_data']
            probability = 1.0 / len(output_skins)  # Equal probability for all outputs
            csfloat_price = output_data['average_price']
              # Calculate what the output float and condition would be using our scaling method
            scaled_float, predicted_condition = self._calculate_output_float_and_condition(average_input_float, output_skin, cheapest_input)
            
            output_details.append({
                'name': output_name,
                'probability': probability,
                'csfloat_price': csfloat_price,
                'expected_float': scaled_float,
                'wear_condition': predicted_condition,
                'skin_data': output_skin,
                'listings': output_data['listings'][:3]  # Show top 3 listings
            })
            
            total_csfloat_expected_value += csfloat_price * probability
        
        # Apply selling fee to CSFloat expected value
        net_csfloat_expected_value = total_csfloat_expected_value * (1 - selling_fee_rate)
        actual_expected_profit = net_csfloat_expected_value - input_purchase_info['total_cost']
        
        # Check if still profitable with real CSFloat data
        if actual_expected_profit <= 0:
            logger.info(f"Trade-up not profitable with actual CSFloat prices. Expected profit: ${actual_expected_profit:.2f}")
            return None
        
        logger.info(f"✅ Profitable trade-up confirmed with CSFloat data! Expected profit: ${actual_expected_profit:.2f}")
        
        # Return comprehensive trade-up analysis
        return {
            'trade_type': 'Single Collection Trade-up',
            'input_collection': collection,
            'input_rarity': input_rarity,
            'output_rarity': output_rarity,
            'input_skin': {
                'name': input_skin_name,
                'quantity_needed': 10,
                'purchase_info': input_purchase_info,
                'skin_data': cheapest_input
            },
            'financial_summary': {
                'total_input_cost': input_purchase_info['total_cost'],
                'expected_output_value': total_csfloat_expected_value,
                'net_expected_value_after_fees': net_csfloat_expected_value,
                'selling_fee_rate': selling_fee_rate,
                'expected_profit': actual_expected_profit,
                'roi_percentage': (actual_expected_profit / input_purchase_info['total_cost']) * 100
            },            'float_analysis': {
                'input_floats': input_floats,
                'average_input_float': average_input_float,
                'input_wear_conditions': [self._get_wear_from_float(f) for f in input_floats],
                'scaling_method': 'Accurate CS2 Float Scaling'
            },
            'output_possibilities': output_details,
            'purchase_instructions': {
                'input_items': input_purchase_info['purchase_plan'],
                'total_items_needed': 10,
                'estimated_completion_time': '2-5 minutes',
                'platform': 'CSFloat Market'
            }
        }
    
    async def close(self) -> None:
        """Clean up resources"""
        # RuntimePricingClient doesn't require cleanup as it uses context managers
        # ComprehensiveDatabaseManager uses local database connections
        # No persistent connections to close        logger.debug("ComprehensiveTradeUpFinder resources cleaned up")
        
    async def _validate_prices(self, prices: Dict[str, Decimal], skins: List[Dict]) -> Dict[str, Decimal]:
        """Validate prices using Steam Market as authoritative source with database tracking"""
        validated_prices = {}
        
        # Create a lookup for skin rarities
        skin_rarity_map = {skin['market_hash_name']: skin.get('rarity', 'Unknown') for skin in skins}
        
        for market_hash_name, price in prices.items():
            price_float = float(price)
            rarity = skin_rarity_map.get(market_hash_name, 'Unknown')
            
            # Skip souvenir skins completely - they can't be traded up
            if 'Souvenir' in market_hash_name:
                logger.debug(f"Skipping souvenir skin {market_hash_name}")
                continue
            
            # Check if we've already validated this skin recently
            validation_status = self.db_manager.get_price_validation_status(market_hash_name)
            
            if validation_status:
                status = validation_status['status']
                
                # If marked as invalid due to large discrepancy, skip it
                if status == 'invalid':
                    logger.debug(f"Skipping {market_hash_name} - previously marked as invalid")
                    continue
                
                # If recently validated as good, use the Steam price
                if status == 'valid' and validation_status['steam_price']:
                    validated_prices[market_hash_name] = Decimal(str(validation_status['steam_price']))
                    logger.debug(f"Using cached Steam price ${validation_status['steam_price']:.2f} for {market_hash_name}")
                    continue
            
            # Need to validate this skin
            logger.info(f"Validating price for {market_hash_name}: ${price_float:.2f}")
            
            validated_price = await self.pricing_client.validate_and_correct_price(
                market_hash_name, price_float, rarity, tolerance_percent=20.0
            )
            
            if validated_price is not None:
                validated_prices[market_hash_name] = Decimal(str(validated_price))
                
                # Mark as valid in database
                steam_price = validated_price
                discrepancy_percent = abs(price_float - validated_price) / validated_price * 100 if validated_price > 0 else 0
                self.db_manager.mark_price_validation_status(
                    market_hash_name, 'valid', steam_price, discrepancy_percent
                )
                
                logger.info(f"Validated {market_hash_name}: ${validated_price:.2f}")
            else:
                # Mark as invalid in database to avoid future Steam API calls
                self.db_manager.mark_price_validation_status(
                    market_hash_name, 'invalid', None, None
                )
                logger.warning(f"Marked {market_hash_name} as invalid - excluding from analysis")
        
        logger.info(f"Price validation complete: {len(validated_prices)}/{len(prices)} prices validated")
        return validated_prices
    
    def _has_price(self, market_hash_name: str) -> bool:
        """Check if we have pricing data for a skin"""
        return market_hash_name in self._cached_prices
    
    def _get_price(self, market_hash_name: str) -> float:
        """Get the price for a skin"""
        price = self._cached_prices.get(market_hash_name, 0)
        return float(price) if price else 0.0
    
    def _is_marketable_skin(self, skin: Dict) -> bool:
        """Check if a skin is marketable (not souvenir, not contraband, StatTrak, etc.)"""
        name = skin.get('market_hash_name', '')
        
        # Skip souvenir items
        if 'Souvenir' in name:
            return False
        
        # Skip StatTrak items (as per CS2 trade-up rules)
        if 'StatTrak™' in name:
            return False
        
        # Skip contraband items
        if skin.get('rarity') == 'Contraband':
            return False
        
        # Skip items without proper market names
        if not name or len(name.strip()) == 0:
            return False
        
        return True
    def _get_condition_float(self, skin: Dict) -> float:
        """Get representative float value for a skin's condition using midpoint of wear category ranges"""
        condition = skin.get('condition_name', 'Field-Tested')
        
        # Use midpoint of each wear category range for calculations
        # Based on CS2 wear ranges: FN(0.00-0.07), MW(0.07-0.15), FT(0.15-0.38), WW(0.38-0.45), BS(0.45-1.00)
        # float_ranges = {
        #     'Factory New': (0.00 + 0.07) / 2,      # 0.035
        #     'Minimal Wear': (0.07 + 0.15) / 2,     # 0.11  
        #     'Field-Tested': (0.15 + 0.38) / 2,     # 0.265
        #     'Well-Worn': (0.38 + 0.45) / 2,        # 0.415
        #     'Battle-Scarred': (0.45 + 1.00) / 2    # 0.725
        # }
        float_ranges = {
            'Factory New': 0.01,      # 0.035
            'Minimal Wear': 0.08,     # 0.11  
            'Field-Tested': 0.16,     # 0.265
            'Well-Worn': 0.39,        # 0.415
            'Battle-Scarred': 0.46    # 0.725
        }
        
        return float_ranges.get(condition, 0.265)
    def _filter_possible_outputs_by_float(self, outputs: List[Dict], input_float: float) -> List[Dict]:
        """All output skins are possible in trade-ups - float gets scaled to each skin's range"""
        # In CS2 trade-ups, all output skins are always possible
        # The input float gets scaled to each output skin's specific float range
        # So we don't need to filter outputs based on float compatibility
        return outputs
    
    async def find_any_positive_return_trade_up(self,
                                              selling_fee_rate: float = 0.15,
                                              target_collections: Optional[List[str]] = None,
                                              min_profit: float = 0.01) -> Optional[Dict]:
        """
        Find any trade-up with positive expected return using available pricing data
        Fallback method when CSFloat validation isn't available
        """
        logger.info(f"Searching for trade-ups with expected profit > ${min_profit:.2f}")
        
        # Get all trade-able rarities
        rarities_to_check = ['Consumer Grade', 'Industrial Grade', 'Mil-Spec Grade', 'Restricted', 'Classified']
        
        for input_rarity in rarities_to_check:
            logger.info(f"Checking {input_rarity} trade-ups...")
            
            # Get collections that have this rarity
            collections = self.db_manager.get_collections_by_rarity(input_rarity)
            
            # Filter to target collections if specified
            if target_collections:
                collections = [c for c in collections if c in target_collections]
            
            for collection in collections:
                # Get input skins from this collection/rarity
                input_skins = self.db_manager.get_skins_by_collection_and_rarity(collection, input_rarity)
                if not input_skins:
                    continue
                
                logger.debug(f"Checking collection: {collection} with {len(input_skins)} input skins")
                
                # Try to find a positive return trade-up for this collection
                result = await self._calculate_simple_tradeup_analysis(
                    collection, input_rarity, input_skins, selling_fee_rate, min_profit
                )
                
                if result:
                    logger.info(f"Found positive return trade-up in {collection}!")
                    return result
        
        logger.info("No positive expected return trade-ups found")
        return None
    
    async def _calculate_simple_tradeup_analysis(self,
                                               collection: str,
                                               input_rarity: str,
                                               input_skins: List[Dict],
                                               selling_fee_rate: float,
                                               min_profit: float) -> Optional[Dict]:
        """Calculate trade-up analysis using standard pricing data"""
        
        # Get output rarity and possible outputs
        rarity_progression = {
            'Consumer Grade': 'Industrial Grade',
            'Industrial Grade': 'Mil-Spec Grade',
            'Mil-Spec Grade': 'Restricted',
            'Restricted': 'Classified',
            'Classified': 'Covert'
        }
        
        output_rarity = rarity_progression.get(input_rarity)
        if not output_rarity:
            return None
        
        # Get possible outputs from the same collection
        output_skins = self.db_manager.get_skins_by_collection_and_rarity(collection, output_rarity)
        if not output_skins:
            return None
        
        # Filter to marketable skins only
        marketable_inputs = [skin for skin in input_skins if self._is_marketable_skin(skin)]
        marketable_outputs = [skin for skin in output_skins if self._is_marketable_skin(skin)]
        
        if not marketable_inputs or not marketable_outputs:
            return None
        
        # Find the cheapest input skin that we can buy 10 of
        cheapest_input = None
        cheapest_price = float('inf')
        
        for skin in marketable_inputs:
            if self._has_price(skin['market_hash_name']):
                price = self._get_price(skin['market_hash_name'])
                if price > 0 and price < cheapest_price:
                    cheapest_input = skin
                    cheapest_price = price
        
        if not cheapest_input:
            return None
        
        # Calculate total input cost (need 10 items)
        input_cost = cheapest_price * 10
          # Calculate expected output value with float scaling
        input_float = self._get_condition_float(cheapest_input)
        total_expected_value = 0
        total_probability = 0
        output_details = []
        
        for output_skin in marketable_outputs:
            if self._has_price(output_skin['market_hash_name']):
                price = self._get_price(output_skin['market_hash_name'])
                if price > 0:                    # Calculate what the output float and condition would be
                    scaled_float, predicted_condition = self._calculate_output_float_and_condition(input_float, output_skin, cheapest_input)
                    
                    # All outputs have equal probability (1/number_of_outputs)
                    probability = 1.0 / len(marketable_outputs)
                    total_expected_value += price * probability
                    total_probability += probability
                    
                    output_details.append({
                        'name': output_skin['market_hash_name'],
                        'probability': probability,
                        'price': price,
                        'collection': collection,
                        'rarity': output_skin['rarity'],
                        'predicted_float': scaled_float,
                        'predicted_condition': predicted_condition,
                        'skin_data': output_skin
                    })
        
        if total_probability == 0:
            return None
        
        # Apply selling fee
        net_expected_value = total_expected_value * (1 - selling_fee_rate)
        expected_profit = net_expected_value - input_cost
        
        logger.debug(f"Analysis: Cost=${input_cost:.2f}, Expected=${net_expected_value:.2f}, Profit=${expected_profit:.2f}")
        
        # Check if profitable
        if expected_profit <= min_profit:
            return None
        
        logger.info(f"✅ Profitable trade-up found! Expected profit: ${expected_profit:.2f}")
        
        # Return comprehensive trade-up analysis
        return {
            'trade_type': 'Single Collection Trade-up',
            'input_collection': collection,
            'input_rarity': input_rarity,
            'output_rarity': output_rarity,
            'validation_method': 'Standard Pricing Data',
            'input_skin': {
                'name': cheapest_input['market_hash_name'],
                'quantity_needed': 10,
                'unit_price': cheapest_price,
                'total_cost': input_cost,
                'skin_data': cheapest_input
            },
            'financial_summary': {
                'total_input_cost': input_cost,
                'expected_output_value': total_expected_value,
                'net_expected_value_after_fees': net_expected_value,
                'selling_fee_rate': selling_fee_rate,
                'expected_profit': expected_profit,
                'roi_percentage': (expected_profit / input_cost) * 100
            },            'float_analysis': {
                'method': 'Accurate CS2 Float Scaling',
                'input_condition': cheapest_input.get('condition_name', 'Field-Tested'),
                'input_float': input_float,
                'scaling_formula': 'output_float = output_min + (input_float * (output_max - output_min))',
                'note': 'Each output skin will have a different predicted condition based on its float range'
            },
            'output_possibilities': output_details,
            'purchase_instructions': {
                'platform': 'Steam Community Market',
                'item_to_buy': cheapest_input['market_hash_name'],
                'quantity': 10,
                'estimated_cost_per_item': cheapest_price,
                'total_estimated_cost': input_cost,
                'note': 'Buy 10 copies of the cheapest input item'
            },
            'recommendations': [
                'Use CSFloat Market for better float precision',
                'Check current market prices before purchasing',
                'Consider float values for optimal outcomes',
                'Verify all items are tradeable before buying'
            ]
        }
    
    def get_market_summary(self) -> Dict:
        """Get a summary of the market data (total skins, collections, etc.)"""
        try:
            # Use the correct method name from ComprehensiveDatabaseManager
            db_stats = self.db_manager.get_database_stats()
            
            summary = {
                'total_skins': db_stats.get('total_skins', 0),
                'unique_weapons': db_stats.get('unique_weapons', 0),
                'unique_collections': db_stats.get('unique_collections', 0),
                'cached_prices': len(self._cached_prices), 
                'by_rarity': db_stats.get('by_rarity', {}),
                'by_category': db_stats.get('by_category', {})
            }
            return summary
        except Exception as e:
            logger.warning(f"Could not get database stats: {e}")
            return {
                'total_skins': 0,
                'unique_weapons': 0,                'unique_collections': 0,
                'cached_prices': len(self._cached_prices),
                'error': str(e)
            }    
    def _calculate_output_float_and_condition(self, input_float: float, output_skin: Dict, input_skin: Dict = None) -> tuple[float, str]:
        """Calculate the actual output float and condition when trading up"""
        output_min = float(output_skin.get('min_float', 0.0))
        output_max = float(output_skin.get('max_float', 1.0))

        print(output_min)
        print(output_max)


        # Use the input skin's actual float range for proper CS:GO/CS2 trade-up scaling
        if input_skin:
            input_min = float(input_skin.get('min_float', 0.0))
            input_max = float(input_skin.get('max_float', 1.0))
        else:
            # Fallback to general CS:GO/CS2 ranges if input skin data not available
            input_min = 0.06
            input_max = 0.8
        
        # Calculate relative position within the input skin's float range
        if input_max > input_min:
            relative_position = (input_float - input_min) / (input_max - input_min)
        else:
            relative_position = 0.0
        
        # Clamp relative position to 0-1 range
        relative_position = max(0.0, min(1.0, relative_position))
        
        # Scale to output skin's range using the relative position
        scaled_output_float = output_min + (relative_position * (output_max - output_min))
        
        # Clamp to skin's range (safety check)
        scaled_output_float = max(output_min, min(output_max, scaled_output_float))
        
        # Determine condition from scaled float
        if scaled_output_float < 0.07:
            condition = "Factory New"
        elif scaled_output_float < 0.15:
            condition = "Minimal Wear"
        elif scaled_output_float < 0.38:
            condition = "Field-Tested"
        elif scaled_output_float < 0.45:
            condition = "Well-Worn"
        else:
            condition = "Battle-Scarred"
            
        return scaled_output_float, condition

    def _get_wear_from_float(self, float_value: float) -> str:
        """Get wear condition name from float value"""
        if float_value < 0.07:
            return "Factory New"
        elif float_value < 0.15:
            return "Minimal Wear"
        elif float_value < 0.38:
            return "Field-Tested"
        elif float_value < 0.45:
            return "Well-Worn"
        else:
            return "Battle-Scarred"
    
    async def _calculate_mixed_collection_tradeup(self,
                                                 primary_collection: str,
                                                 secondary_collection: str,
                                                 input_rarity: str,
                                                 primary_input_skins: List[Dict],
                                                 secondary_input_skins: List[Dict],
                                                 split: Tuple[int, int],
                                                 max_input_price: Optional[float],
                                                 min_profit: float) -> Optional[TradeUpResult]:
        """Calculate mixed collection trade-up following CS:GO trade-up rules"""
        
        # Get output rarity
        rarity_progression = {
            'Consumer Grade': 'Industrial Grade',
            'Industrial Grade': 'Mil-Spec Grade',
            'Mil-Spec Grade': 'Restricted',
            'Restricted': 'Classified',
            'Classified': 'Covert'
        }
        
        output_rarity = rarity_progression.get(input_rarity)
        if not output_rarity:
            return None
        
        primary_count, secondary_count = split
        
        # Get possible outputs from both collections
        primary_output_skins = self.db_manager.get_skins_by_collection_and_rarity(primary_collection, output_rarity)
        secondary_output_skins = self.db_manager.get_skins_by_collection_and_rarity(secondary_collection, output_rarity)
        
        # Filter to marketable skins only
        marketable_primary_inputs = [skin for skin in primary_input_skins if self._is_marketable_skin(skin)]
        marketable_secondary_inputs = [skin for skin in secondary_input_skins if self._is_marketable_skin(skin)]
        marketable_primary_outputs = [skin for skin in primary_output_skins if self._is_marketable_skin(skin)]
        marketable_secondary_outputs = [skin for skin in secondary_output_skins if self._is_marketable_skin(skin)]
        
        if not marketable_primary_inputs or not marketable_secondary_inputs:
            return None
        if not marketable_primary_outputs or not marketable_secondary_outputs:
            return None
        
        # Get pricing data for all items
        all_input_names = [skin['market_hash_name'] for skin in marketable_primary_inputs + marketable_secondary_inputs]
        all_output_names = [skin['market_hash_name'] for skin in marketable_primary_outputs + marketable_secondary_outputs]
        all_names = list(set(all_input_names + all_output_names))
        
        missing_prices = [name for name in all_names if name not in self._cached_prices]
        if missing_prices:
            new_prices = await self.pricing_client.fetch_prices_for_items(missing_prices)
            validated_prices = await self._validate_prices(new_prices, marketable_primary_inputs + marketable_secondary_inputs + marketable_primary_outputs + marketable_secondary_outputs)
            self._cached_prices.update(validated_prices)
        
        # Find cheapest inputs for each collection
        cheapest_primary = self._find_cheapest_input(marketable_primary_inputs, max_input_price)
        cheapest_secondary = self._find_cheapest_input(marketable_secondary_inputs, max_input_price)
        
        if not cheapest_primary or not cheapest_secondary:
            return None
        
        # Calculate total input cost
        primary_cost = cheapest_primary['price'] * primary_count
        secondary_cost = cheapest_secondary['price'] * secondary_count
        total_input_cost = primary_cost + secondary_cost
        
        # Calculate probabilities using trade-up formula
        k_primary = len(marketable_primary_outputs)
        k_secondary = len(marketable_secondary_outputs)
        sum_over_collections = primary_count * k_primary + secondary_count * k_secondary
        
        if sum_over_collections == 0:
            return None
        
        # Calculate expected output value
        expected_output_value = 0
        output_skin_objects = []
        
        # Primary collection outputs
        for output_skin in marketable_primary_outputs:
            price = self._cached_prices.get(output_skin['market_hash_name'])
            if price and float(price) > 0:
                probability = (primary_count * k_primary) / sum_over_collections / k_primary
                expected_output_value += float(price) * probability
                
                skin_obj = Skin(
                    name=output_skin['market_hash_name'],
                    rarity=output_skin['rarity'],
                    price=Decimal(str(price)),
                    collection=primary_collection,
                    float_min=output_skin.get('min_float', 0.0),
                    float_max=output_skin.get('max_float', 1.0)
                )
                output_skin_objects.append(OutputSkin(skin=skin_obj, probability=probability))
        
        # Secondary collection outputs
        for output_skin in marketable_secondary_outputs:
            price = self._cached_prices.get(output_skin['market_hash_name'])
            if price and float(price) > 0:
                probability = (secondary_count * k_secondary) / sum_over_collections / k_secondary
                expected_output_value += float(price) * probability
                
                skin_obj = Skin(
                    name=output_skin['market_hash_name'],
                    rarity=output_skin['rarity'],
                    price=Decimal(str(price)),
                    collection=secondary_collection,
                    float_min=output_skin.get('min_float', 0.0),
                    float_max=output_skin.get('max_float', 1.0)
                )
                output_skin_objects.append(OutputSkin(skin=skin_obj, probability=probability))
        
        if not output_skin_objects:
            return None
        
        # Apply Steam market fee (15%)
        expected_output_value *= 0.85
        expected_profit = expected_output_value - total_input_cost
        
        if expected_profit < min_profit:
            return None
        
        # Create input configuration
        primary_skin = Skin(
            name=cheapest_primary['skin']['market_hash_name'],
            rarity=cheapest_primary['skin']['rarity'],
            price=Decimal(str(cheapest_primary['price'])),
            collection=primary_collection,
            float_min=cheapest_primary['skin'].get('min_float', 0.0),
            float_max=cheapest_primary['skin'].get('max_float', 1.0)
        )
        
        secondary_skin = Skin(
            name=cheapest_secondary['skin']['market_hash_name'],
            rarity=cheapest_secondary['skin']['rarity'],
            price=Decimal(str(cheapest_secondary['price'])),
            collection=secondary_collection,
            float_min=cheapest_secondary['skin'].get('min_float', 0.0),
            float_max=cheapest_secondary['skin'].get('max_float', 1.0)
        )
        
        # Calculate combined float
        primary_float = self._get_condition_float(cheapest_primary['skin'])
        secondary_float = self._get_condition_float(cheapest_secondary['skin'])
        average_float = (primary_float * primary_count + secondary_float * secondary_count) / 10
        
        trade_input = TradeUpInput(
            collection1=primary_collection,
            collection2=secondary_collection,
            split_ratio=(primary_count, secondary_count),
            skins=[primary_skin] * primary_count + [secondary_skin] * secondary_count,
            total_cost=Decimal(str(total_input_cost)),
            average_float=average_float
        )
        
        return TradeUpResult(
            input_config=trade_input,
            output_skins=output_skin_objects,
            expected_output_price=Decimal(str(expected_output_value)),
            raw_profit=Decimal(str(expected_profit)),
            roi_percentage=float(expected_profit / total_input_cost * 100),
            guaranteed_profit=False,
            min_output_price=min(Decimal(str(skin.skin.price)) for skin in output_skin_objects)
        )

    def _find_cheapest_input(self, input_skins: List[Dict], max_input_price: Optional[float]) -> Optional[Dict]:
        """Find the cheapest input skin with valid pricing"""
        cheapest = None
        cheapest_price = float('inf')
        
        for skin in input_skins:
            price = self._cached_prices.get(skin['market_hash_name'])
            if price and float(price) > 0:
                if not max_input_price or float(price) <= max_input_price:
                    if float(price) < cheapest_price:
                        cheapest = {'skin': skin, 'price': float(price)}
                        cheapest_price = float(price)
        
        return cheapest

    def get_pricing_source_info(self) -> Dict:
        """Get information about the current pricing source"""
        if self.use_steam_pricing:
            try:
                stats = self.pricing_client.get_pricing_stats()
                return {
                    'source': 'Steam Market API',
                    'type': 'Steam Market Database',
                    'total_prices': stats.get('total_prices', 0),
                    'average_price': stats.get('average_price', 0.0),
                    'description': 'Real-time Steam Market pricing data'
                }
            except Exception as e:
                return {
                    'source': 'Steam Market API',
                    'type': 'Steam Market Database',
                    'error': str(e),
                    'description': 'Steam Market pricing (error getting stats)'
                }
        else:
            return {
                'source': 'External API',
                'type': 'Runtime Pricing Client',
                'description': 'External pricing API with Steam validation'
            }
    
    def _extract_base_skin_name(self, market_hash_name: str) -> str:
        """Extract base skin name without condition (Factory New, Minimal Wear, etc.)"""
        # Remove condition suffixes
        conditions = ['(Factory New)', '(Minimal Wear)', '(Field-Tested)', '(Well-Worn)', '(Battle-Scarred)']
        for condition in conditions:
            if condition in market_hash_name:
                return market_hash_name.replace(f' {condition}', '').strip()
        
        # If no condition found, return as is
        return market_hash_name
