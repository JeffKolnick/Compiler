import re
import sys
import traceback
from collections import defaultdict

from keywords import KEYWORDS, LITERALS, TOKEN_TYPES, FIRST, FOLLOW

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_tokens(tokens, file_path):
    with open(file_path, 'w') as file:
        for token in tokens:
            file.write(f"{token[0]}: {token[1]}\n")

def write_errors(errors, file_path):
    with open(file_path, 'w') as file:
        for error in errors:
            file.write(f"{error}\n")


input_text = read_file("Test9.cp")

# Run the lexer and parser
lexer = Lexer(input_text)
tokens = lexer.getNextToken()
errors = lexer.errors

parser = Parser(tokens, lexer)
ast = parser.parse()
errors.extend(parser.errors)
symbol_table = SymbolTable()

write_tokens(tokens, "tokens.txt")
if errors:
    write_errors(errors, "errors.txt")
    print("Errors found. Check errors.txt for details.")
else:
    print("Parsing successful.")

with open("ast_output.txt", "w") as f:
    sys.stdout = f
    print("\nAbstract Syntax Tree:")
    parser.print()
    sys.stdout = sys.__stdout__

with open("st_output.txt", "w") as f:
    sys.stdout = f
    print("\nSymbol table:")
    parser.symbol_table.display()
    sys.stdout = sys.__stdout__

icg = IntermediateCodeGenerator(ast, symbol_table)
icg.generate()  

with open("icg_output.txt", "w") as f:
    sys.stdout = f    
    icg.display()
    sys.stdout = sys.__stdout__
