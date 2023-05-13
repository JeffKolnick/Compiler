class SymbolTable:
    def __init__(self):
        self.global_scope = {}
        self.current_scope = self.global_scope
        self.scope_stack = []

    def enter_scope(self):
        new_scope = {}
        self.current_scope = new_scope
        self.scope_stack.append(new_scope)

    def exit_scope(self):
        if self.scope_stack:
            self.scope_stack.pop()
            if len(self.scope_stack) > 0:
                self.current_scope = self.scope_stack[-1]
            else:
                self.current_scope = None
        else:
            print("Error: Trying to exit a non-existent scope.")

    def create_new_scope(self):
        return {}

    def set_current_scope(self, scope):
        self.current_scope = scope

    def get_child(self, node, child_type):
        for child in node.children:
            if child.type == child_type:
                return child
        return None

    def insert(self, line, lexeme, token, symbol_type=None, param_types=None):
        entry = {
            'line': line,
            'lexeme': lexeme,
            'token': token,
            'type': symbol_type,
            'param_types': param_types,
        }

        print(f"Inserting {entry} into symbol table.")
        self.current_scope[lexeme] = entry

        self.display()

    def lookup(self, lexeme, scope=None):
        if scope is None:
            scope = self.current_scope

        if lexeme in scope:
            return scope[lexeme]
        elif 'parent' in scope:
            return self.lookup(lexeme, scope['parent'])
        else:
            return None
        
    def add_function(self, function_name, return_type, param_types, current_token):
        if function_name in self.current_scope:
            self.error(f"Function '{function_name}' already declared in the current scope.", current_token)

        function_info = {
            'line': current_token[2],
            'lexeme': function_name,
            'token': current_token[0],
            'type': return_type,
            'param_types': param_types
        }
        self.current_scope[function_name] = function_info
        self.current_function = function_info

    def end_function(self):
        self.exit_scope()

    def add_function_parameters(self, params_nodes, current_token):
        print(f"Adding parameters in {params_nodes}")
        for param in params_nodes:
            param_name = param.value
            param_type = param.type
            print(f"Adding parameter {param_name} of type {param_type} to Symbol Table")
            self.insert(
                line=current_token[2],
                lexeme=param_name,
                token='ID',
                symbol_type=param_type,
                param_types=param_type
            )
        
    def update_parameter_type(self, param_name, param_type, scope):
        print(f"Updating parameter {param_name} to type {param_type}")
        if param_name in scope:
            scope[param_name]['type'] = param_type
        else:
            print(f"Error: Parameter {param_name} not found in the current scope.")
    
    def get_current_function_info(self):
        for symbol_info in reversed(list(self.global_scope.values())):
            if symbol_info['token'] == 'DEF':
                return symbol_info
        return None

    def display(self, scope=None, indent=0):
        if scope is None:
            scope = self.global_scope
            print("Displaying Global Scope:")  
        else:
            print(f"Displaying scope at indent level {indent}:")  

        for key, value in scope.items():
            if key != 'parent':
                formatted_value = value.copy()
                if isinstance(value['type'], Node):
                    formatted_value['type'] = value['type'].type
                if isinstance(value['param_types'], list):
                    formatted_value['param_types'] = [param.type if isinstance(param, Node) else param for param in value['param_types']]
                print('  ' * indent, key, ":", formatted_value)
                if 'scope' in value:
                    self.display(value['scope'], indent + 1)
