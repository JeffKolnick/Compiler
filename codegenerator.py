class IntermediateCodeGenerator:

    def __init__(self, ast, symbol_table):
        self.ast = ast
        self.type_count = 0
        self.temp_count = 0
        self.ic_code = []
        self.asm_code = []
        self.errors = []
        self.symbol_table = symbol_table

    def new_temp(self):
        temp_name = f"t{self.temp_count}"
        self.temp_count += 1
        return temp_name

    def new_type(self):
        type_name = f"L{self.type_count}"
        self.type_count += 1
        return type_name
    
    def get_child(self, node, child_type=None):
        if node is None:
            self.error(None, f"Error: node is None in get_child({child_type})")
            return None

        for child in node.children:
            if child is not None and (child_type is None or child.type == child_type):
                print(f"Found {node.type} child: {child.type}, {child_type}")
                return child

        print(f"Child not found: {child_type}")
        return None
    
    def traverse_ast(self, node, visited=None):
        if not node:
            return

        if visited is None:
            visited = set()

        if node in visited:
            print(f"Cycle detected: {node.type}")
            return

        visited.add(node)

        if isinstance(node, str):
            node_type = node
        elif isinstance(node, list):
            for child in node:
                self.traverse_ast(child, visited)
            return
        else:
            node_type = node.type

        if node_type == "program":
            self.handle_program(node)
        else:
            handler_name = f"handle_{node_type}"
            handler = getattr(self, handler_name, None)
            if handler:
                handler(node)
            else:
                if hasattr(node, 'children'):
                    for child in node.children:
                        self.traverse_ast(child, visited)

    def generate(self):
        self.traverse_ast(self.ast)
        return self.ic_code

    def handle_program(self, node):
        if node is not None:
            print(f"Entering handle_program with node: {node.type}")
            print(f"Children of program node: {node.children}")

            fdecls_node = self.get_child(node, 'fdecls')
            declarations_node = self.get_child(node, 'declarations')
            statement_seq_node = self.get_child(node, 'statement_seq')

            if fdecls_node is None:
                self.error(None, "Error: fdecls_node is None in handle_program")
            else:
                self.handle_fdecls(fdecls_node)

            if declarations_node is None:
                self.error(None, "Error: declarations_node is None in handle_program")
            else:
                self.handle_declarations(declarations_node)

            if statement_seq_node is None:
                self.error(None, "Error: statement_seq_node is None in handle_program")
            else:
                self.handle_statement_seq(statement_seq_node)

        else:
            self.error(None, "Error: node is None in handle_program")

    def handle_fdecls(self, node):
        if node is not None:
            print(f"Entering handle_fdecls with node: {node.type}")
            fdec_node = self.get_child(node, 'fdec')
            fdecls_prime_node = self.get_child(node, 'fdecls\'')

            if fdec_node:
                self.handle_fdec(fdec_node)
            else:
                self.error(None, "Error: fdec_node is None in handle_fdecls")

            if fdecls_prime_node:
                self.handle_fdecls(fdecls_prime_node)
            else:
                return
        else:
            self.error(None, "Error: node is None in handle_fdecls")

    def handle_fdec(self, node):
        print(f"Entering handle_fdec with node: {node.type}")
        if node is not None:
            return_type_node = self.get_child(node, 'return_type')
            function_name_node = self.get_child(node, 'function_name')
            params_node = self.get_child(node, 'params')
            declarations_node = self.get_child(node, 'declarations')
            statement_seq_node = self.get_child(node, 'statement_seq')

            self.handle_return(return_type_node)
            function_name = self.handle_id(function_name_node)

            self.ic_code.append(f"('FUNC', {function_name})")
            self.ic_code.append(f"('LABEL' {function_name}'_start'")
            self.asm_code.append(f"func {function_name}") 
            self.asm_code.append(f"{function_name}_start")

            self.handle_params(params_node)
            self.handle_declarations(declarations_node)


            if statement_seq_node and statement_seq_node.type == "statement_seq":
                self.handle_statement_seq(statement_seq_node)
            else:
                self.error(None, "Error: statement_seq_node is not of type statement_seq in handle_fdec")

        else:
            self.error(None, "Error: node is None in handle_fdec")

    def handle_id(self, node):
        print(f"Entering handle_id with node: {node.type}")
        if node is not None:
            return node.value
        else:
            self.error(None, "Error: node is None in handle_id")

    def handle_declarations(self, node):
        if node is not None:
            print(f"Entering handle_declarations with node: {node.type}")
            if node.children:
                print(f"Node children: {node.children}")
                for child in node.children:
                    if child:
                        print(f"Child type: {child.type}")
                        if child.type == "decl":
                            self.handle_decl(child)
                            print(f"Node child: {child.children}")
                            var_type = child.children[1][0].type
                            var_name = child.children[1][0].value
                            print(f"var_name, var_type: {var_name}, {var_type}")

                            if self.symbol_table.lookup(var_name) is None:
                                self.symbol_table.insert(None, var_name, 'ID', var_type, None)
                            else:
                                self.error(child.children[0], f"Error: Redeclaration of variable '{var_name}'")

                            print(f"var_name: {var_name}")
                            self.ic_code.append(f"ALLOC {var_name}")
                            self.asm_code.append(f"subq $8, %rsp")
        else:
            self.error(None, "Error: node is None in handle_declarations")

    def handle_decl(self, node):
        function_name = node.value
        if function_name: 
            if node is not None:
                print(f"Entering handle_decl with node: {node.type}")
                type_node = self.get_child(node, 'type')
                var_node = self.get_child(node, 'var')
                
                if type_node and var_node and type_node.children and var_node.children:
                    var_type = type_node.children[0].value
                    var_name = var_node.children[0].value
                    print(f"Declaring variable '{var_name}' of type '{var_type}'")
                    self.insert(line=None, lexeme=var_name, token='ID', symbol_type=var_type)

                    self.ic_code.append(("ALLOC", var_type, var_name))
                    self.asm_code.append(f"subq $8, %rsp  # Allocate memory for variable {var_name}")
                else:
                    self.error(None, f"Error: Invalid declaration for node {node}")
            else:
                self.error(None, "Error: node is None in handle_decl")


    def handle_statement_seq(self, node):
        if node is not None:
            print(f"Entering handle_statement_seq with node: {node.type}")
            print(f"statement_seq node: {node}")
            print(f"statement_seq node children: {node.children}")
            for child in node.children:
                if isinstance(child, Node):
                    if child.type == "assignment_statement":
                        print(f"assignment_statement child: {child}")
                        self.handle_assignment(child)
                    elif child.type == "return_statement":
                        print(f"return_statement child: {child}")
                        self.handle_return(child)
                    elif child.type == "if_statement":
                        print(f"if_statement child: {child}")
                        self.ic_code.append(("(IF {child.children[0]})"))
                        self.ic_code.append(("(COMP _t1, _t2)"))
                        self.asm_code.append(f"CMP _t1, _t2")
                        self.asm_code.append(f"BEQ ret")                        
                    elif child.type == "print_statement":
                        print(f"return_statement child: {child}")
                        self.handle_print(child)
        else:
            self.error(None, "Error: node is None in handle_statement_seq")

    def handle_params(self, node):
        if node is not None:
            print(f"Entering handle_params with node: {node.type} {node.children}")
            for param_node in node.children:
                self.handle_param(param_node)
        else:
            self.error(None, "Error: node is None in handle_params")

    def handle_param(self, param_node):
        print(f"Entering handle_param with node: {param_node.type} {param_node.children}")
        if param_node is not None:
            #param_type_node = self.get_child(param_node, 'type')
            param_type = param_node.type if param_node is not None else None

            #param_var_node = self.get_child(param_node, 'name')
            param_var = param_node.value if param_node is not None else None

            self.ic_code.append(("PARAM", param_type, param_var))
            self.asm_code.append(f"param {param_type} {param_var}")
            self.symbol_table.insert(line=None, lexeme=param_var, token='ID', symbol_type=param_type)
        else:
            self.error(None, "Error: param_node is None in handle_param")
    
    def handle_fname(self, node):
        if node is not None:
            print(f"Entering handle_fname with node: {node.type}")
            function_name = node.value
            args_node = self.get_child(node, 'exprseq')
            args = self.handle_exprseq(args_node)
            print(f"args_node: {args_node}, args: {args}")
            result_temp = self.new_temp()
            self.ic_code.append((result_temp, "CALL", function_name, args))
            self.asm_code.append(f"{result_temp} = call {function_name} {', '.join(args)}")

            return result_temp
        else:
            self.error(None, "Error: node is None in handle_fname")
            return None

    def handle_statement(self, node):
        if node is not None:
            print(f"Entering handle_statement with node: {node.type}")
            if node.is_terminal:
                return

            if node.type == 'var = expr':
                var_node = self.get_child(node, 'var')
                expr_node = self.get_child(node, 'expr')
                var_name = self.handle_var(var_node)
                expr_result = self.handle_expr(expr_node)
                self.ic_code.append(f"{var_name} = {expr_result}")
                self.asm_code.append(f"store {expr_result}, {var_name}")
            elif node.type == 'if bexpr then statement_seq else_part fi':
                bexpr_node = self.get_child(node, 'bexpr')
                then_node = self.get_child(node, 'statement_seq')
                else_node = self.get_child(node, 'else_part')

                self.handle_if(bexpr_node, then_node, else_node)
            elif node.type == 'while <bexpr> do statement_seq od':
                bexpr_node = self.get_child(node, 'bexpr')
                statement_seq_node = self.get_child(node, 'statement_seq')

                self.handle_while(bexpr_node, statement_seq_node)
            elif node.type == 'print expr':
                expr_node = self.get_child(node, 'expr')
                expr_result = self.handle_expr(expr_node)
                self.ic_code.append(f"print {expr_result}")
                self.asm_code.append(f"print {expr_result}")
            elif node.type == 'return expr':
                expr_node = self.get_child(node, 'expr')
                expr_result = self.handle_expr(expr_node)
                self.ic_code.append(f"return {expr_result}")
                self.asm_code.append(f"return {expr_result}")

            for child in node.children:
                self.handle_statement(child)
        else:
            self.error(None, "Error: node is None in handle_statement")

    def handle_if(self, bexpr_node, then_node, else_node):
        if bexpr_node is not None and then_node is not None and else_node is not None:
            print(f"Entering handle_if with nodes: {bexpr_node.type, then_node.type, else_node.type}")
            bexpr_result = self.handle_bexpr(bexpr_node)
            false_label = self.new_label()
            end_label = self.new_label()

            self.ic_code.append(("IF_FALSE", bexpr_result, false_label))
            self.asm_code.append(f"cmpq $0, {bexpr_result}")
            self.asm_code.append(f"je {false_label}")

            self.handle_statement_seq(then_node)

            self.ic_code.append(("GOTO", end_label))
            self.asm_code.append(f"jmp {end_label}")
            self.asm_code.append(f"{false_label}:")

            self.handle_else_part(else_node, end_label)
            self.ic_code.append((end_label, "LABEL"))
            self.asm_code.append(f"{end_label}:")
        else:
            self.error(None, "Error: one or more of bexpr_node, then_node, and else_node is None in handle_if")

    def handle_while(self, bexpr_node, statement_seq_node):
        if bexpr_node is not None and statement_seq_node is not None:
            print(f"Entering handle_while with node: {bexpr_node.type, statement_seq_node.type}")
            start_label = self.new_label()
            end_label = self.new_label()

            self.ic_code.append((start_label, "LABEL"))
            self.asm_code.append(f"{start_label}:")

            bexpr_result = self.handle_bexpr(bexpr_node)
            self.ic_code.append(("IF_FALSE", bexpr_result, end_label))
            self.asm_code.append(f"cmpq $0, {bexpr_result}")
            self.asm_code.append(f"je {end_label}")

            self.handle_statement_seq(statement_seq_node)

            self.ic_code.append(("GOTO", start_label))
            self.asm_code.append(f"jmp {start_label}")
            self.ic_code.append((end_label, "LABEL"))
            self.asm_code.append(f"{end_label}:")
        else:
            self.error(None, "Error: one or more of bexpr_node and statement_seq_node is None in handle_while")

    def handle_else_part(self, node, end_label):
        if node is not None and end_label is not None:
            print(f"Entering handle_else_part with node: {node.type}")
            if node.is_terminal:
                return

            if node.type == 'else statement_seq':
                statement_seq_node = self.get_child(node, 'statement_seq')
                if statement_seq_node is not None:
                    self.handle_statement_seq(statement_seq_node)
                else:
                    self.error(None, "Error: statement_seq_node is None in handle_else_part")

            self.ic_code.append((end_label, "LABEL"))
            self.asm_code.append(f"{end_label}:")
        else:
            self.error(None, "Error: one or more of node and end_label is None in handle_else_part")

    def handle_binop(self, node, left_temp, right_temp):
        if node is not None and left_temp is not None and right_temp is not None:
            print(f"Entering handle_binop with node: {node.type}")
            operator = node.type
            result_temp = self.new_temp()

            self.ic_code.append(f"{result_temp} = {left_temp} {operator} {right_temp}")
            asm_operator = self.asm_operator_mapping.get(operator)
            if asm_operator is not None:
                self.asm_code.append(f"{result_temp} = {left_temp} {asm_operator} {right_temp}")
            else:
                self.error(None, f"Error: unsupported operator {operator} in handle_binop")

            return result_temp
        else:
            self.error(None, "Error: one or more of node, left_temp, and right_temp is None in handle_binop")

    def handle_expression(self, node):
        if node is not None:
            term_node = self.get_child(node, 'term')
            print(f"Entering handle_expression with node: {node}, term_node: {term_node}")
            if term_node is not None:
                left_type, left_temp = self.handle_term(term_node)
                expr_prime_node = self.get_child(node, 'expr\'')
                print(f"left_type: {left_type}, left_temp: {left_temp}, expr_prime_node: {expr_prime_node}")
                if expr_prime_node is None or expr_prime_node.is_terminal:
                    return left_type, left_temp

                right_type, right_temp = self.handle_expression(expr_prime_node.children[1])
                binop_result = self.handle_binop(expr_prime_node.children[0], left_temp, right_temp)
                print(f"right_type: {right_type}, right_temp: {right_temp}, binop_result: {binop_result}")
                self.asm_code.append(f"movq {left_temp}, %rax")
                if expr_prime_node.children[0].type == "PLUS":
                    self.asm_code.append(f"addq {right_temp}, %rax")
                elif expr_prime_node.children[0].type == "MINUS":
                    self.asm_code.append(f"subq {right_temp}, %rax")
                self.asm_code.append(f"movq %rax, {binop_result}")

                return left_type, binop_result

        self.error(None, "Error: node is None in handle_expression")
        return None, None

    def handle_term(self, node):
        if node is not None:
            print(f"Entering handle_term with node: {node}")
            factor_node = self.get_child(node, 'factor')
            print(f"factor_node: {factor_node}")
            if factor_node is not None:
                left_type, left_temp = self.handle_factor(factor_node)
                term_prime_node = self.get_child(node, 'term\'')
                print(f"left_type: {left_type}, left_temp: {left_temp}, term_prime_node: {term_prime_node}")
                if term_prime_node is None or term_prime_node.is_terminal:
                    return left_type, left_temp

                right_type, right_temp = self.handle_term(term_prime_node.children[1])
                binop_result = self.handle_binop(term_prime_node.children[0], left_temp, right_temp)
                print(f"right_type: {right_type}, right_temp: {right_temp}, binop_result: {binop_result}")
                self.asm_code.append(f"movq {left_temp}, %rax")
                if term_prime_node.children[0].type == "TIMES":
                    self.asm_code.append(f"imulq {right_temp}, %rax")
                elif term_prime_node.children[0].type == "DIVIDE":
                    self.asm_code.append(f"cqto")
                    self.asm_code.append(f"idivq {right_temp}")
                self.asm_code.append(f"movq %rax, {binop_result}")

                return left_type, binop_result

        self.error(None, "Error: node is None in handle_term")
        return None, None

    def handle_factor(self, node):
        if node is not None:
            print(f"Entering handle_factor with node: {node.type}")

            if node.children:
                child = node.children[0]
                print(f"child: {child}")

                if child.type == 'var':
                    var_type, var_temp = self.handle_var(child)
                    print(f"var_type: {var_type}, var_temp: {var_temp}")
                    self.ic_code.append(("LOAD_VAR", var_temp))
                    self.asm_code.append(f"movq {var_temp}, %rax")
                    return var_type, var_temp
                elif child.type == 'number':
                    num_type, num_temp = self.handle_number(child)
                    print(f"num_type: {num_type}, num_temp: {num_temp}")
                    self.ic_code.append(("LOAD_NUM", num_temp))
                    self.asm_code.append(f"movq ${num_temp}, %rax")
                    return num_type, num_temp
                elif child.type == '(':
                    return self.handle_expression(node.children[1])
                else:
                    return self.handle_fname(child)
            else:
                self.error(None, "Error: factor node has no children in handle_factor")
                return None, None
        else:
            self.error(None, "Error: node is None in handle_factor")
            return None, None

    def handle_exprseq(self, node):
        if node is not None:
            print(f"Entering handle_exprseq with node: {node.type}")
            expr_values = []

            if node.children:
                expr_node = node.children[0]
                expr_temp = self.handle_expression(expr_node)
                expr_values.append(expr_temp)

                exprseq_prime_node = self.get_child(node, 'exprseq\'')
                while exprseq_prime_node.children:
                    expr_node = exprseq_prime_node.children[1]
                    expr_temp = self.handle_expression(expr_node)
                    expr_values.append(expr_temp)
                    exprseq_prime_node = self.get_child(exprseq_prime_node, 'exprseq\'')

            return expr_values
        else:
            self.error(None, "Error: node is None in handle_exprseq")

    def handle_bexpr(self, node):
        if node is not None:
            print(f"Entering handle_bexpr with node: {node.type}")

            bterm_node = self.get_child(node, 'bterm')
            bexpr_result = self.handle_bterm(bterm_node)

            bexpr_prime_node = self.get_child(node, 'bexpr\'')
            while bexpr_prime_node.children:
                bterm_node = bexpr_prime_node.children[1]
                new_bexpr_result = self.handle_bterm(bterm_node)
                temp = self.new_temp()

                self.ic_code.append((temp, "OR", bexpr_result, new_bexpr_result))
                self.asm_code.append(f"movq {bexpr_result}, %rax")
                self.asm_code.append(f"orq {new_bexpr_result}, %rax")
                self.asm_code.append(f"movq %rax, {temp}")

                bexpr_result = temp
                bexpr_prime_node = self.get_child(bexpr_prime_node, 'bexpr\'')

            return bexpr_result
        else:
            self.error(None, "Error: node is None in handle_bexpr")

    def handle_bterm(self, node):
        if node is not None:
            print(f"Entering handle_bterm with node: {node.type}")

            bfactor_node = self.get_child(node, 'bfactor')
            bterm_result = self.handle_bfactor(bfactor_node)

            bterm_prime_node = self.get_child(node, 'bterm\'')
            while bterm_prime_node.children:
                bfactor_node = bterm_prime_node.children[1]
                new_bterm_result = self.handle_bfactor(bfactor_node)
                temp = self.new_temp()

                self.ic_code.append((temp, "AND", bterm_result, new_bterm_result))
                self.asm_code.append(f"movq {bterm_result}, %rax")
                self.asm_code.append(f"andq {new_bterm_result}, %rax")
                self.asm_code.append(f"movq %rax, {temp}")

                bterm_result = temp
                bterm_prime_node = self.get_child(bterm_prime_node, 'bterm\'')

            return bterm_result
        else:
            self.error(None, "Error: node is None in handle_bterm")

    def handle_comp(self, node):
        if node is not None:
            print(f"Entering handle_comp with node: {node.type}")
            comp_operator = node.children[0].value
            left_expr_node = node.children[1]
            right_expr_node = node.children[2]

            left_expr_result = self.handle_expression(left_expr_node)
            right_expr_result = self.handle_expression(right_expr_node)

            result_temp = self.new_temp()
            self.ic_code.append((result_temp, comp_operator, left_expr_result, right_expr_result))

            # Generate assembly code for comparison
            self.asm_code.append(f"movq {left_expr_result}, %rax")
            self.asm_code.append(f"cmpq {right_expr_result}, %rax")

            # Generate assembly code for conditional set based on the comparison operator
            if comp_operator == "<":
                self.asm_code.append(f"setl %al")
            elif comp_operator == "<=":
                self.asm_code.append(f"setle %al")
            elif comp_operator == ">":
                self.asm_code.append(f"setg %al")
            elif comp_operator == ">=":
                self.asm_code.append(f"setge %al")
            elif comp_operator == "==":
                self.asm_code.append(f"sete %al")
            elif comp_operator == "!=":
                self.asm_code.append(f"setne %al")

            self.asm_code.append(f"movzbq %al, {result_temp}")

            return result_temp
        else:
           self.error(None, "Error: node is None in handle_comp")

    def handle_var(self, node):
        if node is not None:
            print(f"Entering handle_var with node: {node}")
            var_name = node.children[0].value
            print(f"var_name: {var_name}")

            symbol_table_entry = self.symbol_table.lookup(var_name)
            if symbol_table_entry is None:
                self.error(None, f"Error: Variable '{var_name}' not found in the symbol table")
                return None, None  
            
            var_type = symbol_table_entry['type']
            print(f"var_type: {var_type}")
            if len(node.children) == 1:
                print(f"Returning var_type: {var_type}, var_name: {var_name}")
                return var_type, var_name
            else:
                index_expr_node = self.get_child(node, 'expr')
                print(f"index_expr_node: {index_expr_node}")
                if index_expr_node is not None:
                    index_type, index_tac = self.handle_expression(index_expr_node)
                    print(f"index_type: {index_type}, index_tac: {index_tac}")
                    if index_type != 'int':
                        self.error(f"Array index must be of type 'int', but got '{index_type}'.")

                    temp = self.new_temp()
                    self.ic_code.append(f"{temp} = {var_name}[{index_tac}]")
                    self.symbol_table.insert(lexeme=temp, token='ID', symbol_type=var_type)

                    # Generate assembly code for accessing array element
                    self.asm_code.append(f"movq {index_tac}, %rax")
                    self.asm_code.append(f"shlq $3, %rax")  
                    self.asm_code.append(f"addq {var_name}, %rax")
                    self.asm_code.append(f"movq (%rax), {temp}")

                    return var_type, temp
        else:
            self.error(None, "Error: node is None in handle_var")
        return None, None  

    def handle_assignment(self, node):
        if node is not None:
            print(f"Entering handle_assignment with node: {node.type}")
            var_node = self.get_child(node, 'var')
            expr_node = self.get_child(node, 'expression')

            var_type, var_tac = self.handle_var(var_node)
            print(f"var_node: {var_node} , expr_node {expr_node} , var_type: {var_type}, var_tac: {var_tac}")
            if var_type is None or var_tac is None:
                self.error(None, f"Error: Unable to handle assignment for {var_node.children[0].value}")
                return

            expr_type, expr_tac = self.handle_expression(expr_node)

            if expr_type is None or expr_tac is None:
                self.error(None, f"Error: Unable to handle expression for {var_node.children[0].value}")
                return

            if var_type != expr_type:
                self.error(None, f"Error: Type mismatch in assignment. '{var_type}' != '{expr_type}'")
                return

            self.ic_code.append((f"{var_tac} =", expr_tac))
            self.asm_code.append(f"movq {expr_tac}, {var_tac}")
        else:
            self.error(None, "Error: node is None in handle_assignment")

    def handle_return(self, node):
        if node is not None:
            print(f"Entering handle_return with node: {node.type}")

            expr_node = self.get_child(node, 'expr')
            print(f"expr_node: {expr_node}")
            if expr_node is not None:
                expr_type, expr_tac = self.handle_expression(expr_node)
                print(f"expr_type: {expr_type}, expr_tac: {expr_tac}")
                if expr_type is None or expr_tac is None:
                    self.error(None, "Error: Unable to handle return expression")
                    return

                self.ic_code.append(("RETURN", expr_tac))
                self.asm_code.append(f"movq {expr_tac}, %rax")
                self.asm_code.append("ret")
            else:
                self.ic_code.append(("RETURN", "None"))
                self.asm_code.append("ret")
        else:
            self.error(None, "Error: node is None in handle_return")

    def handle_number(self, node):
        if node is not None:
            print(f"Entering handle_number with node: {node.type}")
            num_value = node.children[0].value
            print(f"num_value: {num_value}")

            num_type = 'int' if isinstance(num_value, int) else 'float'

            return num_type, num_value
        else:
            self.error(None, "Error: node is None in handle_number")
            return None, None

    def handle_print(self, node):
        if node is not None:
            print(f"Entering handle_print with node: {node.type}")
            expr_node = self.get_child(node, 'expression')
            print(f"expr_node: {expr_node}")
            if expr_node is not None:
                self.ic_code.append(("PRINT"))
                self.asm_code.append("call print")
            else:
                self.error(None, "Error: node is None in handle_print")
        else:
            self.error(None, "Error: node is None in handle_print")

    def error(self, token, message):
        print(f"Entering error with token: {token}")
        #traceback.print_stack()
        if token is not None and len(token) >= 4:
            line, position = token[2], token[3]
            self.errors.append(f"Error at line {line}, position {position}: {message}")
        else:
            self.errors.append(f"Error: {message}")
            
    def display(self):
        print("Intermediate Code:")
        for ic in self.ic_code:
            print(ic)
        print("Assembly Code:")
        for asm in self.asm_code:
            print(asm)
