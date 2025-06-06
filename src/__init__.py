# filepath: c:\repos\CSTA\src\__init__.py
"""
CS2 Trade-up Calculator Package
"""

from .trade_up_finder import TradeUpFinder, create_finder, find_best_trades, find_guaranteed_trades
from .models import Skin, TradeUpResult, TradeUpInput, OutputSkin
from .formatter import format_trade_up_result, format_trade_up_results, format_results_table
from .logging_config import setup_logging

__version__ = "1.0.0"
__author__ = "CS2 Trade-up Calculator"

__all__ = [
    'TradeUpFinder',
    'create_finder', 
    'find_best_trades',
    'find_guaranteed_trades',
    'Skin',
    'TradeUpResult',
    'TradeUpInput', 
    'OutputSkin',
    'format_trade_up_result',
    'format_trade_up_results',
    'format_results_table',
    'setup_logging'
]