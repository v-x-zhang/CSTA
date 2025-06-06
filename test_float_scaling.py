"""
Test script to verify float scaling implementation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder

def test_float_scaling():
    """Test the float scaling calculation method"""
    
    # Create a mock output skin with known float range
    test_output_skin = {
        'market_hash_name': 'AK-47 | Redline (Field-Tested)',
        'min_float': 0.15,
        'max_float': 0.38,
        'rarity': 'Classified',
        'collection': 'The Huntsman Collection'
    }
    
    # Create instance to test the method
    finder = ComprehensiveTradeUpFinder()
    
    print("🧪 Testing Float Scaling Implementation")
    print("=" * 50)
    print(f"Test Skin: {test_output_skin['market_hash_name']}")
    print(f"Skin Float Range: {test_output_skin['min_float']} - {test_output_skin['max_float']}")
    print()
    
    # Test different input floats
    test_inputs = [
        (0.035, "Factory New"),      # FN midpoint
        (0.11, "Minimal Wear"),      # MW midpoint  
        (0.265, "Field-Tested"),     # FT midpoint
        (0.415, "Well-Worn"),        # WW midpoint
        (0.725, "Battle-Scarred")    # BS midpoint
    ]
    
    print("Input Float → Scaled Output Float (Condition)")
    print("-" * 50)
    
    for input_float, input_condition in test_inputs:
        scaled_float, predicted_condition = finder._calculate_output_float_and_condition(
            input_float, test_output_skin
        )
        
        print(f"{input_float:.3f} ({input_condition}) → {scaled_float:.6f} ({predicted_condition})")
    
    print()
    print("✅ Float scaling test completed!")
    
    # Test edge cases
    print("\n🔬 Testing Edge Cases:")
    print("-" * 30)
    
    # Test with skin that has full float range
    full_range_skin = {
        'market_hash_name': 'Test Skin (Full Range)',
        'min_float': 0.0,
        'max_float': 1.0,
        'rarity': 'Consumer Grade',
        'collection': 'Test Collection'
    }
    
    print(f"Full Range Skin (0.0 - 1.0):")
    for input_float, input_condition in test_inputs[:3]:  # Test first 3
        scaled_float, predicted_condition = finder._calculate_output_float_and_condition(
            input_float, full_range_skin
        )
        print(f"  {input_float:.3f} → {scaled_float:.6f} ({predicted_condition})")

if __name__ == "__main__":
    test_float_scaling()
