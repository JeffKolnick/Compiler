class Lexer:
    def __init__(self, input_text):
        self.input_text = input_text
        self.buffer_size = 2048
        self.buffer1 = input_text[:self.buffer_size]
        self.buffer2 = input_text[self.buffer_size:self.buffer_size * 2]
        self.current_buffer = 1
        self.position = 0
        self.current_char = self.buffer1[self.position]
        self.errors = []
        self.line = 1
        self.column = 1

    def advance(self):
        self.position += 1

        if self.current_buffer == 1:
            if self.position < len(self.buffer1):
                self.current_char = self.buffer1[self.position]
            else:
                self.current_buffer = 2
                self.position = 0
                self.buffer2 = self.input_text[self.buffer_size * (self.current_buffer - 1):self.buffer_size * self.current_buffer]
                self.current_char = self.buffer2[self.position] if self.position < len(self.buffer2) else None
        elif self.current_buffer == 2:
            if self.position < len(self.buffer2):
                self.current_char = self.buffer2[self.position]
            else:
                self.current_char = None

    def getNextToken(self):
        tokens = []
        while self.current_char is not None:
            if self.current_char.isspace():
                if self.current_char == '\n':
                    self.line += 1
                    self.column = 1
                else:
                    self.column += 1
                self.advance()
            else:
                token = self._match_token()
                if token:
                    token_with_position = (token[0], token[1], self.line, self.column)
                    tokens.append(token_with_position)
                    self.column += len(token[1])
                else:
                    self.errors.append(f"Unexpected character '{self.current_char}' at line {self.line}, column {self.column}")
                    self.column += 1
                    self.advance()
        return tokens

    def _match_token(self):
        for pattern, token_type in TOKEN_TYPES.items():
            regex = re.compile(pattern)
            current_buffer = self.buffer1 if self.current_buffer == 1 else self.buffer2
            match = regex.match(current_buffer, self.position)
            if match:
                self.position += len(match.group())
                if self.current_buffer == 1:
                    self.current_char = self.buffer1[self.position] if self.position < len(self.buffer1) else None
                else:
                    self.current_char = self.buffer2[self.position] if self.position < len(self.buffer2) else None

                return token_type, match.group()
        return None
