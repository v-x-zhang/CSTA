"""
Simple debug test for the comprehensive trade finder
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports...")

try:
    from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
    print("✓ ComprehensiveTradeUpFinder imported successfully")
except ImportError as e:
    print(f"✗ Failed to import ComprehensiveTradeUpFinder: {e}")
    sys.exit(1)

try:
    from src.csfloat_listings import CSFloatListingsClient
    print("✓ CSFloatListingsClient imported successfully")
except ImportError as e:
    print(f"✗ Failed to import CSFloatListingsClient: {e}")
    sys.exit(1)

print("\nTesting database connection...")
try:
    finder = ComprehensiveTradeUpFinder()
    print("✓ Database connection successful")
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    sys.exit(1)

print("\nTesting method existence...")
if hasattr(finder, 'find_positive_return_with_csfloat_validation'):
    print("✓ find_positive_return_with_csfloat_validation method exists")
else:
    print("✗ find_positive_return_with_csfloat_validation method not found")
    sys.exit(1)

print("\nAll basic tests passed! Ready to run the comprehensive finder.")
