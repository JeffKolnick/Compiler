class Node:
    def __init__(self, type, value=None, children=None):
        self.type = type
        self.value = value
        if children is not None:
            self.children = children
        else:
            self.children = []

    def __str__(self):
        return f"Node({self.type})"
    
    def __repr__(self):
        return str(self)

class Parser:
    def __init__(self, tokens, lexer):
        self.tokens = tokens
        self.lexer = lexer
        self.symbol_table = SymbolTable()
        self.ast = None
        self.position = 0
        self.current_token = tokens[self.position]
        self.errors = []
        self.reached_end_of_input = False

    def advance(self):
        if self.position + 1 < len(self.tokens):
            self.position += 1
            self.current_token = self.tokens[self.position]
        else:
            self.reached_end_of_input = True
        print(self.current_token)

    def panic_mode_recovery(self, non_terminal):
        recovery_tokens = FOLLOW[non_terminal]
        print(f"PAN!C MODE recovery for {non_terminal}, current token: {self.current_token}")

        if non_terminal in ['<term>', '<factor>']:
            recovery_tokens = recovery_tokens.union(FIRST[non_terminal])

        while self.current_token and self.current_token[0] not in recovery_tokens:
            if self.reached_end_of_input:
                break
            self.advance()

    def lookahead(self):
        if self.position + 1 < len(self.tokens):
            return self.tokens[self.position + 1]
        else:
            return None
        
    def parse(self):
        self.ast = self.parse_program()
        return self.ast

    def parse_program(self):
        print(f"Entering parse_program with token: {self.current_token}")
        if self.current_token and (self.current_token[0] in FIRST['<program>']):
            fdecls = self.parse_fdecls()
            print(f"Completed parse_fdecls. AST state: {self.ast} Node: {fdecls}")

            declarations = self.parse_declarations()
            print(f"Completed parse_declarations. AST state: {self.ast} Node: {declarations}")

            statement_seq = self.parse_statement_seq()
            print(f"Completed parse_statement_seq. AST state: {self.ast} Node: {statement_seq}")

            if self.current_token and self.current_token[0] == 'PERIOD':
                self.advance()
            else:
                self.error(f"Unexpected token '{self.current_token[0]}' at the end of the program. Expected 'PERIOD'.")
                self.panic_mode_recovery('<program>')

            program_node = Node('program', value="program_node", children=[
                Node('fdecls', value="fdecls_node", children=fdecls.children if fdecls else []), 
                Node('declarations', value="declarations_node", children=declarations.children if declarations else []), 
                Node('statement_seq', value="statement_seq_node", children=statement_seq.children if statement_seq else [])
            ])
            #self.ast = program_node
            print(f"Completed parse_program. AST state: {program_node}")
            return program_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' at the beginning of the program.")
            self.panic_mode_recovery('<program>')

    def parse_fdecls(self):
        print(f"Entering parse_fdecls with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<fdecls>']:
            if self.current_token[0] == 'DEF':
                fdec = self.parse_fdec()
                self.match_terminal('SEMICOLON', '<fdecls>')  
                fdecls_prime = self.parse_fdecls_prime()
                fdecls_node = Node('fdecls', children=[fdec, fdecls_prime])
                print(f"Completed parse_fdecls. AST state: {fdecls_node}") 
                return fdecls_node
        elif self.current_token and self.current_token[0] in FOLLOW['<fdecls>']:
            fdecls_node = Node('fdecls', value="fdecls_node")
            print(f"Completed parse_fdecls. AST state: {fdecls_node}")  
            #self.ast = fdecls_node
            return fdecls_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in function declaration.")
            self.panic_mode_recovery('<fdecls>')
            if self.current_token and self.current_token[0] in FOLLOW['<fdecls>']:
                self.error(f"Recovered from unexpected token '{self.current_token[0]}' in function declaration.")

    def parse_fdecls_prime(self):
        print(f"Entering parse_fdecls_prime with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<fdecls\'>']:
            fdec = self.parse_fdecls()
            fdecls_prime_node = Node('fdecls_prime', value="fdecls_prime_node", children=[fdec, fdecls_prime])
            print(f"Completed parse_fdecls_prime. AST state: {fdecls_prime_node}")
            return fdecls_prime_node
        elif self.current_token and self.current_token[0] in FOLLOW['<fdecls\'>']:
            fdecls_prime = Node('fdecls_prime', value="fdecls_prime_node")
            print(f"Completed parse_fdecls_prime. AST state: {fdecls_prime}")  
            return fdecls_prime
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in function declaration.")
            self.panic_mode_recovery('<fdecls\'>')

    def parse_fdec(self):
        print(f"Entering parse_fdec with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<fdec>']:
            self.match_terminal('DEF', '<fdec>')
            return_type = self.parse_type()
            function_name = self.current_token[1]
            self.parse_fname()

            self.match_terminal('LPAREN', '<fdec>')
            param_types_node = self.parse_params(param_count=0)
            self.match_terminal('RPAREN', '<fdec>')

            # Add the function to the symbol table and set it as the current function
            self.symbol_table.add_function(function_name, return_type=return_type, param_types=param_types_node.children, current_token=self.current_token)
            function_scope = self.symbol_table.create_new_scope()
            self.symbol_table.set_current_scope(function_scope)

            # Add function parameters to the symbol table
            for param, param_type in zip(param_types_node.children, self.symbol_table.current_function['param_types']):
                self.symbol_table.insert(self.current_token[2], param.value, 'ID', param_type)

            declarations = self.parse_declarations()
            statement_seq = self.parse_statement_seq()
            self.symbol_table.set_current_scope(self.symbol_table.global_scope)

            self.match_terminal('FED', '<fdec>')
            fdec_node = Node('fdec', value="fdec_node", children=[Node('return_type', value=return_type), Node('function_name', value=function_name), param_types_node, declarations, statement_seq])
            print(f"Completed parse_fdec. AST state: {fdec_node}")  
            self.ast = fdec_node
            return fdec_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in fdec.")
            self.panic_mode_recovery('<fdec>')

    def parse_params(self, param_count=0):
        print(f"Entering parse_params with token: {self.current_token}")
        params = []
        if self.current_token and self.current_token[0] in FIRST['<params>']:
            param_type_node = self.parse_type()      
            print(f"param_type_node: {param_type_node}")      
            param_name_token = self.match_terminal('ID', '<params>')
            param_name = param_name_token[1]  
            param_type = param_type_node.type
            param_token = param_name_token[0]
            print(f"param_type: {param_type}, param_name: {param_name}, param_token: {param_token}")
            params.append(Node(type=param_type, value=param_name))
            params += self.parse_params_prime(param_count + 1).children
        elif self.current_token and self.current_token[0] in FOLLOW['<params>']:
            pass
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in function parameters.")
            self.panic_mode_recovery('<params>')
        params_node = Node('params', value="params_node", children=params)
        print(f"Completed parse_params. AST state: {params_node}")
        return params_node

    def parse_params_prime(self, param_count=0):
        print(f"Entering parse_params_prime with token: {self.current_token}")
        params = []
        if self.current_token and self.current_token[0] in FIRST['<params\'>']:
            self.match_terminal('COMMA', '<params\'>')
            params_node = self.parse_params(param_count + 1)
            params += params_node.children
        elif self.current_token and self.current_token[0] in FOLLOW['<params\'>']:
            pass
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in function parameters.")
            self.panic_mode_recovery('<params\'>')
        params_node = Node('params_prime', value="params_prime_node", children=params)
        print(f"Completed parse_params_prime. AST state: {params_node}")
        return params_node

    def parse_fname(self):
        print(f"Entering parse_fname with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<fname>']:
            function_name = self.current_token[1]
            self.match_terminal('ID', '<fname>')
            
            function_name_node = Node('ID', value="params_prime_node", children=[function_name])
            print(f"Completed parse_fname. AST state: {function_name, function_name_node}")
            return function_name_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in function name.")
            self.panic_mode_recovery('<fname>')

    def parse_declarations(self):
        print(f"Entering parse_declarations with token: {self.current_token}")
        declarations = []
        if self.current_token and self.current_token[0] in FIRST['<declarations>']:
            decl = self.parse_decl()
            self.match_terminal('SEMICOLON', '<declarations>')
            declarations.append(decl)
            declarations.append(self.parse_declarations_prime())
        elif self.current_token and self.current_token[0] in FOLLOW['<declarations>']:
            declarations_node = Node('declarations', value="declarations_node")
            print(f"Completed parse_declarations. AST state: {declarations_node}")
            return declarations_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in declaration.")
            self.panic_mode_recovery('<declarations>')
        declarations_node = Node('declarations', value="declarations_node", children=declarations)
        print(f"Completed parse_declarations. AST state: {declarations_node}")  
        self.ast = declarations_node
        return declarations_node

    def parse_declarations_prime(self):
        print(f"Entering parse_declarations_prime with token: {self.current_token}")
        declarations = []
        if self.current_token and self.current_token[0] in FIRST['<declarations\'>']:
            decl = self.parse_decl()
            self.match_terminal('SEMICOLON', '<declarations\'>')
            declarations.append(decl)
            declarations.extend(self.parse_declarations_prime())
        elif self.current_token and self.current_token[0] in FIRST['<statement>']:
            pass
        elif self.current_token and self.current_token[0] in FOLLOW['<declarations\'>']:
            declarations_node = Node('declarations_prime', value="declarations_prime_node")
            print(f"Completed parse_declarations_prime. AST state: {declarations_node}")
            return declarations_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in declaration.")
            self.panic_mode_recovery('<declarations\'>')
        declarations_node = Node('declarations_prime', value="declarations_prime_node", children=declarations)
        print(f"Completed parse_declarations_prime. AST state: {declarations_node}")
        return declarations_node

    def parse_decl(self):
        print(f"Entering parse_decl with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<decl>']:
            token_type, lexeme, line, column = self.current_token
            symbol_type = lexeme  
            self.match_terminal(token_type, '<decl>')

            varlist = []
            while self.current_token and self.current_token[0] in FIRST['<varlist>']:
                token_type, var_lexeme, var_line, var_column = self.current_token

                """ # Insert the variable into the symbol table
                self.symbol_table.insert(var_line, var_lexeme, token_type, symbol_type) """
                varlist_node = self.parse_varlist()
                varlist.append(varlist_node)

            return Node('decl', children=[Node('type', children=[symbol_type])] + varlist)
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in declaration.")
            self.panic_mode_recovery('<decl>')

    def parse_type(self):
        print(f"Entering parse_type with token: {self.current_token}")
        if self.current_token and self.current_token[0] == 'INT_TYPE':
            self.match_terminal('INT_TYPE', '<type>')
            type_node = Node(type='INT_TYPE', value="type_node")
            print(f"Completed parse_type. AST state: {type_node}")
            return type_node
        elif self.current_token and self.current_token[0] == 'DOUBLE_TYPE':
            self.match_terminal('DOUBLE_TYPE', '<type>')
            type_node = Node(type='DOUBLE_TYPE', value="type_node")
            print(f"Completed parse_type. AST state: {type_node}")
            return type_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in type.")
            self.panic_mode_recovery('<type>')

    def parse_varlist(self):
        print(f"Entering parse_varlist with token: {self.current_token}")
        varlist = []
        if self.current_token and self.current_token[0] in FIRST['<varlist>']:
            var_node = self.parse_var()
            varlist.append(var_node)
            varlist_prime_node = self.parse_varlist_prime()
            varlist.extend(varlist_prime_node.children)
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in variable list.")
            self.panic_mode_recovery('<varlist>')
        varlist_node = Node('varlist', value="varlist_node", children=varlist)
        print(f"Completed parse_varlist. AST state: {varlist_node}")
        return varlist_node.children

    def parse_varlist_prime(self):
        print(f"Entering parse_varlist_prime with token: {self.current_token}")
        varlist = []
        if self.current_token and self.current_token[0] in FIRST['<varlist\'>']:
            self.match_terminal('COMMA', '<varlist\'>')
            var_node = self.parse_var()
            varlist.append(var_node)
            varlist_prime_node = self.parse_varlist_prime()
            varlist.extend(varlist_prime_node.children)
        elif self.current_token and self.current_token[0] in FOLLOW['<varlist\'>']:
            varlist_node = Node('varlist_prime', value="varlist_prime_node", children=[])
            print(f"Completed parse_varlist_prime. AST state: {varlist_node}")
            return varlist_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in variable list.")
            self.panic_mode_recovery('<varlist\'>')
        varlist_node = Node('varlist_prime', value="varlist_prime_node", children=varlist)
        print(f"Completed parse_varlist_prime. AST state: {varlist_node}")
        return varlist_node

    def parse_statement_seq(self):
        print(f"Entering parse_statement_seq with token: {self.current_token}")
        statements = []
        if self.current_token and self.current_token[0] in FIRST['<statement_seq>']:
            statement_node = self.parse_statement()
            statements.append(statement_node)
            statement_seq_prime_node = self.parse_statement_seq_prime()
            statements.extend(statement_seq_prime_node.children)
        elif self.current_token and self.current_token[0] in FOLLOW['<statement_seq>']:
            statement_seq_node = Node('statement_seq', children=[])
            print(f"Completed parse_statement_seq. AST state: {statement_seq_node}")  
            return statement_seq_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in statement sequence.")
            self.panic_mode_recovery('<statement_seq>')
        statement_seq_node = Node('statement_seq', value="statement_seq_node", children=statements)
        print(f"Completed parse_statement_seq. AST state: {statement_seq_node}")  
        self.ast = statement_seq_node
        return statement_seq_node

    def parse_statement_seq_prime(self):
        print(f"Entering parse_statement_seq_prime with token: {self.current_token}")
        statements = []
        if self.current_token and self.current_token[0] in FIRST['<statement_seq\'>']:
            self.match_terminal('SEMICOLON', '<statement_seq\'>')
            statement_node = self.parse_statement()
            statements.append(statement_node)
            statement_seq_prime_node = self.parse_statement_seq_prime()
            statements.extend(statement_seq_prime_node.children)
        elif self.current_token and self.current_token[0] in FOLLOW['<statement_seq\'>']:
            statement_seq_prime_node = Node('statement_seq_prime', value="statement_seq_prime_node", children=[])
            print(f"Completed parse_statement_seq_prime. AST state: {statement_seq_prime_node}")  
            return statement_seq_prime_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in statement sequence.")
            self.panic_mode_recovery('<statement_seq\'>')
        statement_seq_prime_node = Node('statement_seq_prime', value="statement_seq_prime_node", children=statements)
        print(f"Completed parse_statement_seq_prime. AST state: {statement_seq_prime_node}")  
        return statement_seq_prime_node

    def parse_statement(self):
        print(f"Entering parse_statement with token: {self.current_token}")
        if self.current_token and self.current_token[0] == 'IF':
            self.match_terminal('IF', '<statement>')
            bexpr_node = self.parse_bexpr()
            self.match_terminal('THEN', '<statement>')
            self.symbol_table.enter_scope()
            statement_seq_node = self.parse_statement_seq()
            else_part_node = self.parse_else_part()
            self.symbol_table.exit_scope()
            self.match_terminal('FI', '<statement>')
            if_statement_node = Node('if_statement', value="if_statement_node", children=[bexpr_node, statement_seq_node, else_part_node])
            print(f"Completed parse_statement. AST state: {if_statement_node}")  
            return if_statement_node
        
        elif self.current_token and self.current_token[0] == 'WHILE':
            self.match_terminal('WHILE', '<statement>')
            bexpr_node = self.parse_bexpr()
            self.match_terminal('DO', '<statement>')
            self.symbol_table.enter_scope()
            statement_seq_node = self.parse_statement_seq()
            self.symbol_table.exit_scope()
            self.match_terminal('OD', '<statement>')
            while_statement_node = Node('while_statement', value="while_statement_node", children=[bexpr_node, statement_seq_node])
            print(f"Completed parse_statement. AST state: {while_statement_node}")  
            return while_statement_node

        elif self.current_token and self.current_token[0] == 'RETURN':
            self.match_terminal('RETURN', '<statement>')
            expression_node = self.parse_expression()
            return_statement_node = Node('return_statement', value="return_statement_node", children=[expression_node])
            print(f"Completed parse_statement. AST state: {return_statement_node}")  
            return return_statement_node

        elif self.current_token and self.current_token[0] == 'PRINT':
            self.match_terminal('PRINT', '<statement>')
            expression_node = self.parse_expression()
            print_statement_node = Node('print_statement', value="print_statement_node", children=[expression_node])
            print(f"Completed parse_statement. AST state: {print_statement_node}")  
            return print_statement_node

        elif self.current_token and self.current_token[0] in FIRST['<var>']:
            var_node = self.parse_var()
            self.match_terminal('ASSIGN', '<statement>')
            expression_node = self.parse_expression()
            assignment_statement_node = Node('assignment_statement', value="assignment_statement_node", children=[var_node, expression_node])
            print(f"Completed parse_statement. AST state: {assignment_statement_node}")  
            return assignment_statement_node

        elif self.current_token and self.current_token[0] in FOLLOW['<statement>']:
            return Node("empty")
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in statement.")
            self.panic_mode_recovery('<statement>')

    def parse_else_part(self):
        print(f"Entering parse_else_part with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<else_part>']:
            self.match_terminal('ELSE', '<else_part>')
            self.symbol_table.enter_scope()
            statement_seq_node = self.parse_statement_seq()
            self.symbol_table.exit_scope()
            else_part_node = Node('else_part', children=[statement_seq_node])
            print(f"Completed parse_else_part. AST state: {else_part_node}")  
            return else_part_node
        elif self.current_token and self.current_token[0] in FOLLOW['<else_part>']:
            return Node("empty")
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in else part.")
            self.panic_mode_recovery('<else_part>')

    def parse_expression(self):
        print(f"Entering parse_expression with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<expr>']:
            left_node = self.parse_term()
            if self.current_token and self.current_token[0] != 'COMP':
                right_node = self.parse_expression_prime(left_node)
                expression_node = Node('expression', value="expression_node", children=[left_node, right_node])
            else:
                expression_node = left_node
            print(f"Completed parse_expression. AST state: {expression_node}")  
            return expression_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in expression.")
            self.panic_mode_recovery('<expr>')

    def parse_expression_prime(self, inherited_node):
        print(f"Entering parse_expression_prime with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<expr\'>']:
            operator_node = Node('operator', children=self.current_token[0])
            self.match_terminal(self.current_token[0], '<expr\'>')
            left_node = inherited_node
            right_node = self.parse_term()
            next_node = self.parse_expression_prime(right_node)
            expression_prime_node = Node('expression_prime', children=[operator_node, left_node, right_node, next_node])
            print(f"Completed expression_prime. AST state: {expression_prime_node}")  
            return expression_prime_node
        elif self.current_token and self.current_token[0] in FOLLOW['<expr\'>']:
            expression_prime_node = Node('expression_prime', value="expression_prime_node", children=[])
            print(f"Completed expression_prime. AST state: {expression_prime_node}")
            return expression_prime_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in expression.")
            self.panic_mode_recovery('<expr\'>')

    def parse_term(self):
        print(f"Entering parse_term with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<term>']:
            left_node = self.parse_factor()
            right_node = self.parse_term_prime(left_node)
            term_node = Node('term', value="term_node", children=[left_node, right_node])
            print(f"Completed parse_term. AST state: {term_node}")  
            return term_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in term.")
            self.panic_mode_recovery('<term>')

    def parse_term_prime(self, inherited_node):
        print(f"Entering parse_term_prime with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<term\'>']:
            operator_node = Node('operator', children=self.current_token[0])
            self.match_terminal(self.current_token[0], '<term\'>')
            left_node = inherited_node
            right_node = self.parse_factor()
            next_node = self.parse_term_prime(right_node)
            term_prime_node = Node('term_prime', value="term_prime_node", children=[operator_node, left_node, right_node, next_node])
            print(f"Completed parse_term_prime. AST state: {term_prime_node}")  
            return term_prime_node
        elif self.current_token and self.current_token[0] in FOLLOW['<term\'>']:
            return Node("empty")
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in term.")
            self.panic_mode_recovery('<term\'>')

    def parse_id(self):
        print(f"Entering parse_id with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<id>']:
            id_value = self.current_token[1]
            id_node = Node('id', value=id_value)
            self.match_terminal('ID', '<id>')
            print(f"Completed parse_id. AST state: {id_node}")
            return id_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in id.")
            self.panic_mode_recovery('<id>')

    def parse_factor(self):
        print(f"Entering parse_factor with token: {self.current_token}")
        if self.current_token and self.current_token[0] == 'LPAREN':
            self.match_terminal('LPAREN', '<factor>')
            expr_node = self.parse_expression()
            self.match_terminal('RPAREN', '<factor>')
            factor_node = Node('factor', value="factor_node", children=['(', expr_node, ')'])
            print(f"Completed parse_factor. AST state: {factor_node}")  
            return factor_node
        elif self.current_token and self.current_token[0] == 'ID':
            next_token = self.lookahead()
            print(f"Factor ID Next token: {next_token}")
            if next_token and next_token[0] == 'LPAREN':
                id_node = self.parse_id()  
                self.match_terminal('LPAREN', '<factor>')
                exprseq_node = self.parse_exprseq()
                self.match_terminal('RPAREN', '<factor>')
                function_call_node = Node('function_call', value="function_call_node", children=[id_node, '(', exprseq_node, ')'])
                print(f"Completed parse_factor. AST state: {function_call_node}")  
                return function_call_node
            else:
                var_node = self.parse_var()
                factor_call_node = Node('factor', value="function_call_node", children=[var_node])
                print(f"Completed parse_factor. AST state: {factor_call_node}")  
                return factor_call_node
        elif self.current_token and self.current_token[0] == 'INT':
            int_node = Node('int', value="int_node", children=self.current_token[1])
            self.match_terminal('INT', '<factor>')       
            factor_node = Node('factor', value="factor_node", children=[int_node])
            print(f"Completed parse_factor. AST state: {factor_node}")  
            return factor_node    
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in factor.")
            self.panic_mode_recovery('<factor>')

    def parse_exprseq(self):
        print(f"Entering parse_exprseq with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<expr>']:
            expr_node = self.parse_expression()
            exprseq_prime_node = self.parse_exprseq_prime()
            exprseq_node = Node('exprseq', children=[expr_node, exprseq_prime_node])
            print(f"Created node: {exprseq_node.type} with children: {exprseq_node.children}")
            return exprseq_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in expression sequence.")
            self.panic_mode_recovery('<exprseq>')

    def parse_exprseq_prime(self):
        print(f"Entering parse_exprseq_prime with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<exprseq\'>']:
            self.match_terminal('COMMA', '<exprseq\'>')
            expr_node = self.parse_expression()
            exprseq_prime_node = self.parse_exprseq_prime()
            exprseq_prime_node = Node('exprseq_prime', value="exprseq_prime_node", children=[',', expr_node, exprseq_prime_node])
            print(f"Created node: {exprseq_prime_node.type} with children: {exprseq_prime_node.children}")
            return exprseq_prime_node
        elif self.current_token and self.current_token[0] in FOLLOW['<exprseq\'>']:
            return Node("empty")
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in expression sequence.")
            self.panic_mode_recovery('<exprseq\'>')

    def parse_bexpr(self):
        print(f"Entering parse_bexpr with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<bexpr>']:
            bterm_node = self.parse_bterm()
            bexpr_prime_node = self.parse_bexpr_prime()

            bexpr_node = Node('bexpr', value="bexpr_node", children=[bterm_node, bexpr_prime_node])
            print(f"Created node: {bexpr_node.type} with children: {bexpr_node.children}")
            return bexpr_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in boolean expression.")
            self.panic_mode_recovery('<bexpr>')

    def parse_bexpr_prime(self, left_expr_node=None, comp_node=None):
        print(f"Entering parse_bexpr_prime with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<bexpr\'>']:
            if left_expr_node is not None and comp_node is not None:
                print(f"Left expr node: {left_expr_node}")
                right_expr_node = self.parse_expression()

            self.match_terminal('OR', '<bexpr\'>')
            bterm_node = self.parse_bterm()
            bexpr_prime_node = self.parse_bexpr_prime()
            bfactor_node = Node('bexpr_prime', value="bfactor_node", children=['OR', bterm_node, bexpr_prime_node])
            print(f"Created node: {bfactor_node.type} with children: {bfactor_node.children}")
            return bfactor_node
        elif self.current_token and self.current_token[0] in FOLLOW['<bexpr\'>']:
            return Node("empty")
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in boolean expression.")
            self.panic_mode_recovery('<bexpr\'>')

    def parse_bterm(self):
        print(f"Entering parse_bterm with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<bterm>']:
            bfactor_node = self.parse_bfactor()
            bterm_prime_node = self.parse_bterm_prime()
            bfactor_node = Node('bterm', value="bfactor_node", children=[bfactor_node, bterm_prime_node])
            print(f"Created node: {bfactor_node.type} with children: {bfactor_node.children}")
            return bfactor_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in boolean term.")
            self.panic_mode_recovery('<bterm>')

    def parse_bterm_prime(self):
        print(f"Entering parse_bterm_prime with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<bterm\'>']:
            self.match_terminal('AND', '<bterm\'>')
            bfactor_node = self.parse_bfactor()
            bterm_prime_node = self.parse_bterm_prime()
            bfactor_node = Node('bfactor', value="bfactor_node", children=['AND', bfactor_node, bterm_prime_node])
            print(f"Created node: {bfactor_node.type} with children: {bfactor_node.children}")
            return bfactor_node
        elif self.current_token and self.current_token[0] in FOLLOW['<bterm\'>']:
            return Node("empty")
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in boolean term.")
            self.panic_mode_recovery('<bterm\'>')

    def parse_bfactor(self):
        print(f"Entering parse_bfactor with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<bfactor>']:
            bfactor_node = Node('bfactor', value="bfactor_node")

            if self.current_token[0] == 'LPAREN':
                self.match_terminal('LPAREN', '<bfactor>')
                if self.current_token[0] in FIRST['<bexpr>']:
                    bexpr_node = self.parse_bexpr()
                    bfactor_node.children.append(bexpr_node)
                    self.match_terminal('RPAREN', '<bfactor>')
                elif self.current_token[0] in FIRST['<expr>']:
                    expr1_node = self.parse_expression()
                    comp_node = self.parse_comp()
                    expr2_node = self.parse_expression()
                    self.match_terminal('RPAREN', '<bfactor>')
                    bfactor_node.children.extend([expr1_node, comp_node, expr2_node])
                else:
                    self.error(f"Unexpected token '{self.current_token[0]}' in bfactor.")
                    self.panic_mode_recovery('<bfactor>')
            elif self.current_token[0] == 'NOT':
                self.match_terminal('NOT', '<bfactor>')
                bfactor_child_node = self.parse_bfactor()
                bfactor_node.children.append(bfactor_child_node)
            else:
                self.error(f"Unexpected token '{self.current_token[0]}' in bfactor.")
                self.panic_mode_recovery('<bfactor>')

            print(f"Completed parse_bfactor. AST state: {bfactor_node}")
            return bfactor_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in bfactor.")
            self.panic_mode_recovery('<bfactor>')

    def parse_comp(self):
        print(f"Entering parse_comp with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<comp>']:
            comp_token = self.current_token[0]
            self.match_terminal(self.current_token[0], '<comp>')
            comp_node = Node('comp', value="comp_node", children=[comp_token])
            print(f"Created node: {comp_node.type} with children: {comp_node.children}")
            return comp_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in comparison operator.")
            self.panic_mode_recovery('<comp>')

    def parse_var(self):
        print(f"Entering parse_var with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<var>']:
            id_node = self.parse_id()
            var_name = id_node.value
            print(f"Var Name: {var_name}")
            index_node = None
            
            if self.current_token and self.current_token[0] == 'LBRACKET':
                self.match_terminal('LBRACKET', '<var>')
                expr_node = self.parse_expression()
                self.match_terminal('RBRACKET', '<var>')
                index_node = Node('index', value="index_node", children=['[', expr_node, ']'])
            var_node = Node('var', value=var_name, children=[id_node, index_node])
            print(f"Created node: {var_node.type} with children: {var_node.children}")
            return var_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in variable.")
            self.panic_mode_recovery('<var>')

    def parse_integer(self):
        print(f"Entering parse_integer with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<digit>']:
            num_token = self.current_token[0]
            self.match_terminal('NUM', '<integer>')
            next_num_node = None

            if self.current_token and self.current_token[0] in FIRST['<digit>']:
                next_num_node = self.parse_integer()
            integer_node = Node('integer', value="integer_node", children=[num_token, next_num_node])
            print(f"Created node: {integer_node.type} with children: {integer_node.children}")
            return integer_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in integer.")
            self.panic_mode_recovery('<integer>')

    def parse_double(self):
        print(f"Entering parse_double with token: {self.current_token}")
        if self.current_token and self.current_token[0] in FIRST['<digit>']:
            integer_node = self.parse_integer()
            frac_node = None

            if self.current_token and self.current_token[0] == 'PERIOD':
                self.match_terminal('PERIOD', '<double>')
                frac_node = self.parse_integer()
            else:
                self.error(f"Unexpected token '{self.current_token[0]}' in double.")
                self.panic_mode_recovery('<double>')
            double_node = Node('double', value="double_node", children=[integer_node, '.', frac_node])
            print(f"Created node: {double_node.type} with children: {double_node.children}")
            return double_node
        else:
            self.error(f"Unexpected token '{self.current_token[0]}' in double.")
            self.panic_mode_recovery('<double>')

    def match_terminal(self, expected_token_type, non_terminal=None):
        print(f"Trying to match {expected_token_type}, current token: {self.current_token}")
        if self.current_token and self.current_token[0] == expected_token_type:
            token_type, lexeme, line, column = self.current_token
            
            if token_type in KEYWORDS or token_type in LITERALS:
                symbol_type = None
                if token_type in LITERALS:
                    symbol_type = lexeme
                """ elif token_type == 'ID':
                    prev_token = self.tokens[self.position - 2] if self.position > 1 else None
                    if prev_token and prev_token[0] in ['INT_TYPE', 'DOUBLE_TYPE']:
                        symbol_type = prev_token[0] """

                self.symbol_table.insert(line, lexeme, token_type, symbol_type)

            matched_token = self.current_token
            print(f"Matched token: {matched_token}, token_type: {token_type}, lexeme: {lexeme}, line: {line}, column: {column}, Advancing from {self.current_token} to ", end="")

            self.advance()
            return matched_token
        elif not self.current_token or self.current_token[0] == 'PERIOD':
            self.error(f"Expected token {expected_token_type}, but found EOF")
        else:
            self.error(f"Expected token {expected_token_type}, but found {self.current_token[0]}")
            if non_terminal:
                self.panic_mode_recovery(non_terminal)
    def error(self, message):
        print(f"Entering error with token: {self.current_token}")
        if len(self.current_token) >= 4:
            line, position = self.current_token[2], self.current_token[3]
            self.errors.append(f"Error at line {line}, position {position}: {message}")
        else:
            self.errors.append(f"Error: {message}") 

    def print(self, node=None, indent=0, visited=None):
        if node is None:
            node = self.ast

        if visited is None:
            visited = set()

        if isinstance(node, list):
            for item in node:
                self.print(item, indent, visited)
        elif isinstance(node, Node):
            if node in visited:
                print(f"Cycle detected: {node.value, node.type}")
                return

            visited.add(node)

            print(" " * (indent // 2) + f"Node {node.value}, {node.type}, children={len(node.children)}, nodes={node.children}")
            for child in node.children:
                self.print(child, indent + 2, visited)
        else:
            print(" " * (indent // 2) + str(node))
