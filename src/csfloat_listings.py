"""
CSFloat Listings Client for real-time float and pricing data
"""
import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Tuple
from decimal import Decimal

try:
    from .config import config
    from .api_client import RateLimiter
except ImportError:
    from config import config
    from api_client import RateLimiter

logger = logging.getLogger(__name__)

class CSFloatListingsClient:
    """Client for fetching actual CSFloat listings with real float values"""
    def __init__(self):
        self.base_url = config.api.CSFLOAT_BASE_URL
        self.api_key = config.api.CSFLOAT_API_KEY
        self.rate_limiter = RateLimiter(config.api.CSFLOAT_RATE_LIMIT)
        
        # Try different authentication methods
        self.auth_headers = [
            {
                'Authorization': f"Bearer {self.api_key}",
                'Content-Type': 'application/json'
            },
            {
                'Authorization': f"{self.api_key}",
                'Content-Type': 'application/json'
            },
            {
                'X-API-Key': f"{self.api_key}",
                'Content-Type': 'application/json'
            }
        ]
        self.current_header_index = 0
    
    async def get_listings_for_skin(self, market_hash_name: str, 
                                   session: aiohttp.ClientSession,
                                   limit: int = 20) -> List[Dict]:
        """Get actual CSFloat listings for a specific skin"""
        await self.rate_limiter.acquire()
        
        url = f"{self.base_url}/listings"
        params = {
            "market_hash_name": market_hash_name,
            "limit": limit,
            "sort_by": "lowest_price",  # Get cheapest listings first
            "type": "buy_now"
        }
        try:
            # Try different authentication methods until one works
            for i, headers in enumerate(self.auth_headers):
                try:
                    logger.debug(f"Trying authentication method {i+1} for {market_hash_name}")
                    async with session.get(url, headers=headers, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            listings = []
                            for item in data:
                                # Extract relevant data from CSFloat listing
                                listing = {
                                    'id': item.get('id'),
                                    'price': float(item.get('price', 0)),
                                    'float': float(item.get('float_value', 0.5)),
                                    'market_hash_name': item.get('market_hash_name', market_hash_name),
                                    'inspect_link': item.get('inspect_link'),
                                    'seller': item.get('seller', {}).get('username', 'Unknown'),
                                    'stickers': item.get('stickers', []),
                                    'wear_rating': self._get_wear_from_float(item.get('float_value', 0.5)),
                                    'url': f"https://csfloat.com/item/{item.get('id', '')}"
                                }
                                listings.append(listing)
                            
                            logger.info(f"✅ Retrieved {len(listings)} CSFloat listings for {market_hash_name}")
                            self.current_header_index = i  # Remember working auth method
                            return listings
                        
                        elif response.status == 403:
                            logger.warning(f"403 Forbidden with auth method {i+1} for {market_hash_name}")
                            continue
                        
                        elif response.status == 429:
                            logger.warning(f"Rate limited by CSFloat API for {market_hash_name}")
                            await asyncio.sleep(2)
                            continue
                        
                        else:
                            logger.warning(f"CSFloat API returned {response.status} with auth method {i+1} for {market_hash_name}")
                            continue
                            
                except Exception as e:
                    logger.warning(f"Error with auth method {i+1} for {market_hash_name}: {e}")
                    continue
            
            # If all auth methods failed
            logger.warning(f"All CSFloat authentication methods failed for {market_hash_name}")
            return []
        except Exception as e:
            logger.error(f"Error fetching CSFloat listings for {market_hash_name}: {e}")
            return []
    
    async def get_multiple_skin_listings(self, skin_names: List[str], 
                                       session: aiohttp.ClientSession,
                                       listings_per_skin: int = 10) -> Dict[str, List[Dict]]:
        """Get listings for multiple skins efficiently"""
        all_listings = {}
        
        for skin_name in skin_names:
            listings = await self.get_listings_for_skin(
                skin_name, session, limit=listings_per_skin
            )
            all_listings[skin_name] = listings
            
            # Small delay to be respectful to API
            await asyncio.sleep(0.1)
        
        return all_listings
    
    def _get_wear_from_float(self, float_value: float) -> str:
        """Convert float value to wear condition"""
        if float_value < 0.07:
            return 'Factory New'
        elif float_value < 0.15:
            return 'Minimal Wear'
        elif float_value < 0.38:
            return 'Field-Tested'
        elif float_value < 0.45:
            return 'Well-Worn'
        else:
            return 'Battle-Scarred'
    
    def scale_float_to_skin_range(self, input_float: float, 
                                 skin_min_float: float, 
                                 skin_max_float: float) -> float:
        """Scale a 0-1 float to a skin's specific float range"""
        # Clamp input float to skin's range
        if input_float < skin_min_float:
            return skin_min_float
        elif input_float > skin_max_float:
            return skin_max_float
        else:
            return input_float
    
    def calculate_average_scaled_float(self, input_floats: List[float], 
                                     input_skins: List[Dict]) -> float:
        """Calculate properly scaled average float for trade-up calculation"""
        if len(input_floats) != len(input_skins):
            raise ValueError("Number of floats must match number of skins")
        
        # Scale each float to 0-1 range based on skin's float range
        scaled_floats = []
        for i, float_val in enumerate(input_floats):
            skin = input_skins[i]
            skin_min = skin.get('min_float', 0.0)
            skin_max = skin.get('max_float', 1.0)
            
            # Scale to 0-1: (float - min) / (max - min)
            if skin_max > skin_min:
                scaled_float = (float_val - skin_min) / (skin_max - skin_min)
            else:
                scaled_float = 0.0  # Edge case where min == max
            
            # Clamp to 0-1 range
            scaled_float = max(0.0, min(1.0, scaled_float))
            scaled_floats.append(scaled_float)
        
        # Return average of scaled floats
        return sum(scaled_floats) / len(scaled_floats)
    
    def calculate_output_float(self, average_scaled_float: float, 
                             output_skin: Dict) -> float:
        """Calculate the actual output float given the scaled average"""
        output_min = output_skin.get('min_float', 0.0)
        output_max = output_skin.get('max_float', 1.0)
        
        # Scale from 0-1 back to output skin's range
        return output_min + (average_scaled_float * (output_max - output_min))
    
    def get_purchase_info(self, listings: List[Dict], quantity_needed: int) -> Dict:
        """Get information about where and how much to buy skins"""
        if not listings:
            return {
                'total_cost': 0,
                'average_float': 0.5,
                'purchase_plan': [],
                'available': False
            }
        
        # Sort by price (cheapest first)
        sorted_listings = sorted(listings, key=lambda x: x['price'])
        
        if len(sorted_listings) < quantity_needed:
            logger.warning(f"Not enough listings available. Need {quantity_needed}, found {len(sorted_listings)}")
        
        # Take the cheapest listings we need
        selected_listings = sorted_listings[:quantity_needed]
        
        total_cost = sum(listing['price'] for listing in selected_listings)
        average_float = sum(listing['float'] for listing in selected_listings) / len(selected_listings)
        
        purchase_plan = []
        for listing in selected_listings:
            purchase_plan.append({
                'price': listing['price'],
                'float': listing['float'],
                'wear': listing['wear_rating'],
                'seller': listing['seller'],
                'url': listing['url'],
                'id': listing['id']
            })
        
        return {
            'total_cost': total_cost,
            'average_float': average_float,
            'purchase_plan': purchase_plan,
            'available': len(selected_listings) >= quantity_needed,
            'listings_found': len(sorted_listings)
        }
