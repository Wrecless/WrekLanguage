# Token handling

#constants
DIGITS = '0123456789'

# Error handling
class Error:
    def __init__(self, pos_start, pos_end, error_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end
        self.error_name = error_name
        self.details = details

    def as_string(self):
        result = f'{self.error_name}: {self.details}\n'  # Add a newline character
        result += f'File {self.pos_start.fn}, line {self.pos_start.ln + 1}'
        return result


class NotSupportedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end,'Character not supported', details)

# Position handling
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def get_next_token(self, current_char):
        self.idx += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.idx, self.ln, self.col, self.fn, self.ftxt)

# TT = Token types
TT_INT = 'INT'
TT_FLOAT = 'FLOAT'
TT_PLUS = 'PLUS'
TT_MINUS = 'MINUS'
TT_MUL = 'MUL'
TT_DIV = 'DIV'
TT_LPAREN = 'LPAREN'
TT_RPAREN = 'RPAREN'

#class Token:
# https://www.digitalocean.com/community/tutorials/python-str-repr-functions
class Token:
    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    #needs to be __repr__ instead of __str__ to be able to return a string
    def __repr__(self):
        if self.value:
            return f'{self.type}:{self.value}'
        return f'({self.type})'

# Lexer
class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.get_next_token()  # Advance to the first character


    def get_next_token(self):
        self.pos.get_next_token(self.current_char)
        if self.pos.idx < len(self.text):
            self.current_char = self.text[self.pos.idx]
        else:
            self.current_char = None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.get_next_token()

            elif self.current_char in DIGITS:
                tokens.append(self.check_number())

            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS))
                self.get_next_token()

            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS))
                self.get_next_token()

            elif self.current_char == '*':
                tokens.append(Token(TT_MUL))
                self.get_next_token()

            elif self.current_char == '/':
                tokens.append(Token(TT_DIV))
                self.get_next_token()

            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN))
                self.get_next_token()

            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN))
                self.get_next_token()

            else:
                pos_start = self.pos.copy()

                char = self.current_char
                self.get_next_token()
                return [], NotSupportedCharError(pos_start, self.pos, "'" + char + "'")

        return tokens , None

    def check_number(self):
        num_str = ''
        dot_count = 0

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.get_next_token()

        if dot_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))

# Nodes
class NumberNode:
    def __init__(self, tok):
        self.tok = tok

    def __repr__(self):
        return f'{self.tok}'

class BinOpNode:
    def __init__(self, left_node, op_tok, right_node):
        self.left_node = left_node
        self.op_tok = op_tok
        self.right_node = right_node

    def __repr__(self):
        return f'({self.left_node}, {self.op_tok}, {self.right_node})'

# Parser
# https://ruslanspivak.com/lsbasi-part1/

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = 1
        self.get_next_token()

    def get_next_token(self):
        self.token_index += 1
        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]
        else:
            self.current_token = None

    def factor(self):
        tok = self.current_token

        if tok.type in (TT_INT, TT_FLOAT):
            self.get_next_token()
            return NumberNode(tok)

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def expression(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))



#run function
def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    return tokens, error