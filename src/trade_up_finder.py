"""
Main orchestrator for the CS2 trade-up calculator.
Coordinates data fetching, caching, calculations, and result formatting.
"""

import asyncio
import logging
from typing import List, Optional
from decimal import Decimal

from .config import config
from .api_client import APIClient
from .database import DatabaseManager
from .calculator import TradeUpCalculator, TradeUpCandidate
from .models import MarketData, TradeUpResult

logger = logging.getLogger(__name__)

class TradeUpFinder:
    """Main application class coordinating all components"""
    def __init__(self, use_mock_data: bool = False, use_profitable_mock: bool = False, limit_items: Optional[int] = None, use_csfloat: bool = False):
        logger.debug(f"TradeUpFinder: use_mock_data={use_mock_data}, use_profitable_mock={use_profitable_mock}")
        self.api_client = APIClient(use_mock_data=use_mock_data, use_profitable_mock=use_profitable_mock, limit_items=limit_items, use_csfloat=use_csfloat)
        self.db_manager = DatabaseManager()
        self.calculator = None
        self.market_data = None
    
    async def initialize(self, force_refresh: bool = False) -> None:
        """Initialize the system with market data"""
        logger.info("Initializing CS2 Trade-up Calculator...")
          # If using mock data, always fetch fresh mock data
        if self.api_client.use_mock_data:
            logger.info("Using mock data - fetching fresh data")
            await self._fetch_and_cache_data()
            # Continue to build market data and calculator
        elif not force_refresh:
            # Try to load cached data first
            self.market_data = self.db_manager.build_market_data()
            if self.market_data:
                logger.info("Using cached market data")
                self.calculator = TradeUpCalculator(self.market_data)
                return
        else:
            # Fetch fresh data from APIs
            logger.info("Fetching fresh market data from APIs...")
            await self._fetch_and_cache_data()
        
        # Build market data object
        self.market_data = self.db_manager.build_market_data()
        if not self.market_data:
            raise RuntimeError("Failed to build market data")
        
        # Initialize calculator
        self.calculator = TradeUpCalculator(self.market_data)
        logger.info("System initialized successfully")
    
    async def _fetch_and_cache_data(self) -> None:
        """Fetch data from APIs and cache it"""
        # Fetch skin data from both APIs
        skins = await self.api_client.fetch_all_market_data()
        
        if not skins:
            raise RuntimeError("Failed to fetch skin data from APIs")
        
        # Cache the data
        self.db_manager.cache_skins(skins)
        logger.info(f"Cached {len(skins)} skins to database")
    
    async def find_profitable_trades(
        self,
        min_profit: float = 0.0,
        max_input_price: Optional[float] = None,
        target_collections: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[TradeUpResult]:
        """
        Find profitable trade-up opportunities
        
        Args:
            min_profit: Minimum profit threshold in dollars
            max_input_price: Maximum price per input skin in dollars
            target_collections: Specific collections to focus on
            limit: Maximum number of results to return
        
        Returns:
            List of profitable trade-up results
        """
        if not self.calculator:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        logger.info(f"Searching for profitable trade-ups (min_profit=${min_profit})")
        
        # Convert parameters
        min_profit_decimal = Decimal(str(min_profit))
        max_price_decimal = Decimal(str(max_input_price)) if max_input_price else None
        
        # Find candidates
        candidates = self.calculator.find_profitable_tradeups(
            min_profit=min_profit_decimal,
            max_input_price=max_price_decimal,
            target_collections=target_collections
        )
        
        # Convert to detailed results
        results = []
        for candidate in candidates[:limit]:
            result = self.calculator.calculate_detailed_result(candidate)
            results.append(result)
        
        logger.info(f"Found {len(results)} profitable trade-up opportunities")
        return results
    
    async def find_guaranteed_profit_trades(
        self,
        max_input_price: Optional[float] = None,
        target_collections: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[TradeUpResult]:
        """Find trade-ups with guaranteed profit (all outputs profitable)"""
        
        if not self.calculator:
            raise RuntimeError("System not initialized. Call initialize() first.")
        
        logger.info("Searching for guaranteed profit trade-ups")
        
        # Convert parameters
        max_price_decimal = Decimal(str(max_input_price)) if max_input_price else None
        
        # Find all candidates
        candidates = self.calculator.find_profitable_tradeups(
            min_profit=Decimal('0'),
            max_input_price=max_price_decimal,
            target_collections=target_collections
        )
        
        # Filter for guaranteed profit only
        guaranteed_candidates = [
            c for c in candidates 
            if c.guaranteed_profit and c.guaranteed_profit > 0
        ]
        
        # Sort by guaranteed profit
        guaranteed_candidates.sort(
            key=lambda c: c.guaranteed_profit, 
            reverse=True
        )
        
        # Convert to results
        results = []
        for candidate in guaranteed_candidates[:limit]:
            result = self.calculator.calculate_detailed_result(candidate)
            results.append(result)
        
        logger.info(f"Found {len(results)} guaranteed profit trade-ups")
        return results
    
    def get_market_summary(self) -> dict:
        """Get summary of current market data"""
        if not self.market_data:
            return {}
        
        summary = {
            'total_collections': len(self.market_data.collections),
            'total_skins': 0,
            'skins_by_rarity': {},
            'last_updated': self.market_data.last_updated
        }
        
        for collection in self.market_data.collections.values():
            for rarity, skins in collection.skins_by_rarity.items():
                summary['total_skins'] += len(skins)
                if rarity not in summary['skins_by_rarity']:
                    summary['skins_by_rarity'][rarity] = 0
                summary['skins_by_rarity'][rarity] += len(skins)
        
        return summary
    
    def get_available_collections(self) -> List[str]:
        """Get list of all available collections"""
        if not self.market_data:
            return []
        
        return list(self.market_data.collections.keys())
    
    async def close(self) -> None:
        """Clean up resources"""
        await self.api_client.close()

# Convenience functions for direct usage
async def create_finder(force_refresh: bool = False) -> TradeUpFinder:
    """Create and initialize a TradeUpFinder instance"""
    finder = TradeUpFinder()
    await finder.initialize(force_refresh=force_refresh)
    return finder

async def find_best_trades(
    min_profit: float = 1.0,
    max_input_price: Optional[float] = None,
    limit: int = 10
) -> List[TradeUpResult]:
    """Quick function to find the best trade-up opportunities"""
    finder = await create_finder()
    try:
        results = await finder.find_profitable_trades(
            min_profit=min_profit,
            max_input_price=max_input_price,
            limit=limit
        )
        return results
    finally:
        await finder.close()

async def find_guaranteed_trades(
    max_input_price: Optional[float] = None,
    limit: int = 5
) -> List[TradeUpResult]:
    """Quick function to find guaranteed profit trades"""
    finder = await create_finder()
    try:
        results = await finder.find_guaranteed_profit_trades(
            max_input_price=max_input_price,
            limit=limit
        )
        return results
    finally:
        await finder.close()
