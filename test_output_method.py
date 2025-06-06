"""
Simple test to check the get_output_collection method
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.comprehensive_database import ComprehensiveDatabaseManager

def test_output_collection():
    print("Testing output collection method...")
    
    try:
        db = ComprehensiveDatabaseManager()
        
        # Test what get_output_collection returns
        result = db.get_output_collection('Consumer Grade')
        print(f"get_output_collection('Consumer Grade') = {result}")
        
        # Check if this method exists and what it does
        print("\nChecking database methods...")
        methods = [method for method in dir(db) if 'output' in method.lower()]
        print(f"Methods with 'output': {methods}")
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    test_output_collection()
