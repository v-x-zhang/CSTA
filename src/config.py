"""
Configuration module for CS2 Trade-up Calculator
Contains API configuration using environment variables for security.
"""

import os
from dataclasses import dataclass
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class APIConfig:
    """Configuration for API endpoints and keys"""
    # API Keys from environment variables
    PRICE_EMPIRE_API_KEY: str = os.getenv('PRICE_EMPIRE_API_KEY', '')
    CSFLOAT_API_KEY: str = os.getenv('CSFLOAT_API_KEY', '')
    
    # API Endpoints
    PRICE_EMPIRE_BASE_URL: str = "https://api.pricempire.com/v4/paid"
    CSFLOAT_BASE_URL: str = "https://csfloat.com/api/v1"
    
    # Rate limiting
    PRICE_EMPIRE_RATE_LIMIT: int = 60  # requests per minute
    CSFLOAT_RATE_LIMIT: int = 60       # requests per minute
    
    # Cache settings
    CACHE_REFRESH_INTERVAL: int = 900  # 15 minutes in seconds
    
    def __post_init__(self):
        """Validate that required API keys are present"""
        if not self.PRICE_EMPIRE_API_KEY:
            raise ValueError(
                "PRICE_EMPIRE_API_KEY environment variable is required. "
                "Please create a .env file with your API key. See .env.example for template."
            )
        if not self.CSFLOAT_API_KEY:
            raise ValueError(
                "CSFLOAT_API_KEY environment variable is required. "
                "Please create a .env file with your API key. See .env.example for template."
            )

@dataclass
class DatabaseConfig:
    """Configuration for database settings"""
    DB_PATH: str = "data/skins.db"
    ENABLE_WAL: bool = True

@dataclass
class TradeUpConfig:
    """Configuration for trade-up calculations"""
    # Rarity mappings
    RARITIES: Dict[str, int] = None
    RARITY_UPGRADES: Dict[str, str] = None
    RARITY_MAPPING: Dict[str, str] = None
    MAX_RESULTS: int = 50
    
    def __post_init__(self):
        if self.RARITIES is None:
            self.RARITIES = {
                "Mil-Spec": 1,
                "Restricted": 2, 
                "Classified": 3,
                "Covert": 4
            }
        
        if self.RARITY_UPGRADES is None:
            self.RARITY_UPGRADES = {
                "Mil-Spec": "Restricted",
                "Restricted": "Classified",
                "Classified": "Covert"
            }
        
        if self.RARITY_MAPPING is None:
            self.RARITY_MAPPING = self.RARITY_UPGRADES

class Config:
    """Main configuration class"""
    def __init__(self):
        self.api = APIConfig()
        self.database = DatabaseConfig()
        self.trade_up = TradeUpConfig()
        
    @property
    def price_empire_headers(self) -> Dict[str, str]:
        """Headers for Price Empire API requests"""
        return {
            "Authorization": f"Bearer {self.api.PRICE_EMPIRE_API_KEY}",
            "Content-Type": "application/json"
        }
    
    @property
    def csfloat_headers(self) -> Dict[str, str]:
        """Headers for CSFloat API requests"""
        return {
            "Authorization": self.api.CSFLOAT_API_KEY,
            "Content-Type": "application/json"
        }

# Global config instance
config = Config()