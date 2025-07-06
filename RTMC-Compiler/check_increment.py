import sys
sys.path.append('.')

from src.lexer.tokenizer import Tokenizer

def check_increment_tokens():
    code = "i++"
    tokenizer = Tokenizer(code)
    tokens = tokenizer.tokenize()
    
    print("Tokens for 'i++':")
    for token in tokens:
        print(f"  {token.type.name}: '{token.value}'")

if __name__ == "__main__":
    check_increment_tokens()
