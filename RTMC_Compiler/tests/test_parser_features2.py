import sys
sys.path.append('.')

from src.lexer.tokenizer import Tokenizer, TokenType
from src.parser.parser import Parser

# Test boolean parsing
def test_boolean_parsing():
    code = """
    void main() {
        bool x = true;
        bool y = false;
        if (x) {
            int z = 1;
        }
        while (y) {
            int w = 2;
        }
    }
    """
    
    tokenizer = Tokenizer(code)
    tokens = tokenizer.tokenize()
    
    parser = Parser(tokens)
    ast = parser.parse()
    
    print("Boolean parsing test passed!")
    return True

# Test brace styles
def test_brace_styles():
    code = """
    void func1() {
        int x = 1;
    }
    
    void func2()
    {
        int y = 2;
    }
    
    void main() 
    {
        if (true) {
            func1();
        }
        
        while (false)
        {
            func2();
        }
    }
    """
    
    tokenizer = Tokenizer(code)
    tokens = tokenizer.tokenize()
    
    parser = Parser(tokens)
    ast = parser.parse()
    
    print("Brace styles test passed!")
    return True

if __name__ == "__main__":
    test_boolean_parsing()
    test_brace_styles()
    print("All tests passed!")
