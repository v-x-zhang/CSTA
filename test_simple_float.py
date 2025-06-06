import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from src.comprehensive_trade_finder import ComprehensiveTradeUpFinder
    print("✅ Import successful")
    
    # Test the float scaling method directly
    finder = ComprehensiveTradeUpFinder()
    
    # Test output skin
    test_skin = {
        'min_float': 0.15,
        'max_float': 0.38
    }
    
    # Test with FT input (0.265)
    input_float = 0.265
    result_float, result_condition = finder._calculate_output_float_and_condition(input_float, test_skin)
    
    print(f"Input: {input_float} → Output: {result_float:.6f} ({result_condition})")
    print("✅ Float scaling test completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
