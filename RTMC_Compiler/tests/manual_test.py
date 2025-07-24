#!/usr/bin/env python3
"""
Manual test of sizeof functionality
"""

def manual_test():
    """Manual test of basic parsing components"""
    # Test if SizeOfExprNode can be imported
    try:
        from RTMC_Compiler.src.parser.ast_nodes import SizeOfExprNode, PrimitiveTypeNode
        print("✓ SizeOfExprNode imported successfully")
        
        # Create a sizeof node manually
        target = PrimitiveTypeNode("int", 1)
        sizeof_node = SizeOfExprNode(target, 1)
        print("✓ SizeOfExprNode created successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    manual_test()
