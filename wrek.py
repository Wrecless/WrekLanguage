import string_with_arrows

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
        result += '\n\n' + string_with_arrows.string_with_arrows(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return result

class NotSupportedCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end,'Character not supported', details)

class InvalidSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=''):
        super().__init__(pos_start, pos_end, 'Invalid syntax', details)

##### POSITION #####
class Position:
    def __init__(self, idx, ln, col, fn, ftxt):
        self.idx = idx
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def get_next_token(self, current_char=None):
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
TT_EOF = 'EOF' # End of file

##### class Token #####
# https://www.digitalocean.com/community/tutorials/python-str-repr-functions
class Token:
    def __init__(self, type_, value=None, pos_start=None, pos_end=None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start.copy()
            self.pos_end = pos_start.copy()
            self.pos_end.get_next_token('')

        if pos_end:
            self.pos_end = pos_end

    #needs to be __repr__ instead of __str__ to be able to return a string
    def __repr__(self):
        if self.value:
            return f'{self.type}:{self.value}'
        return f'({self.type})'

##### Lexer #####
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
                tokens.append(Token(TT_PLUS, pos_start=self.pos))
                self.get_next_token()

            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start=self.pos))
                self.get_next_token()

            elif self.current_char == '*':
                tokens.append(Token(TT_MUL, pos_start=self.pos))
                self.get_next_token()

            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start=self.pos))
                self.get_next_token()

            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start=self.pos))
                self.get_next_token()

            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start=self.pos))
                self.get_next_token()

            else:
                pos_start = self.pos.copy()

                char = self.current_char
                self.get_next_token()
                return [], NotSupportedCharError(pos_start, self.pos, "'" + char + "'")

        tokens.append(Token(TT_EOF, pos_start=self.pos))
        return tokens , None

    def check_number(self):
        num_str = ''
        dot_count = 0
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.get_next_token()

        if dot_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

##### NODES #####
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

class UnaryOpNode:
    def __init__(self, op_tok, node):
        self.op_tok = op_tok
        self.node = node

    def __repr__(self):
        return f'({self.op_tok}, {self.node})'

##### Parse Result #####
class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, res):
        if isinstance(res, ParseResult):
            if res.error: self.error = res.error
            return res.node
        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self

##### Parser #####
# https://ruslanspivak.com/lsbasi-part1/
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.token_index = -1
        self.get_next_token()

    def get_next_token(self):
        self.token_index += 1
        if self.token_index < len(self.tokens):
            self.current_token = self.tokens[self.token_index]

        return self.current_token

    def parse(self):
        res = self.expression()
        if not res.error and self.current_token.type != TT_EOF:
            return res.failure(InvalidSyntaxError(self.current_token.pos_start, self.current_token.pos_end, "Expected '+', '-', '*', or '/'"))
        return res

##############################################
# Grammar
# expression = term ((PLUS | MINUS) term)*
    def factor(self):
        response = ParseResult()
        tok = self.current_token

        # Check if the token is a plus or minus
        if tok.type in (TT_PLUS, TT_MINUS):
            response.register(self.get_next_token())
            factor = response.register(self.factor())
            if response.error: return response
            return response.success(UnaryOpNode(tok, factor))

        # Check if the token is an int or float
        elif tok.type in (TT_INT, TT_FLOAT):
            response.register(self.get_next_token())
            return response.success(NumberNode(tok))

        # Check if the token is a left parenthesis
        elif tok.type == TT_LPAREN:
            response.register(self.get_next_token())
            expression = response.register(self.expression())
            if response.error: return response
            if self.current_token.type == TT_RPAREN:
                response.register(self.get_next_token())
                return response.success(expression)
            else:
                return response.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Expected ')'"))

        return response.failure(InvalidSyntaxError(tok.pos_start, tok.pos_end, "Expected int or float"))

    def term(self):
        return self.bin_op(self.factor, (TT_MUL, TT_DIV))

    def expression(self):
        return self.bin_op(self.term, (TT_PLUS, TT_MINUS))

# Binary operation
    def bin_op(self, func, ops):
        response = ParseResult()
        left = response.register(func())
        if response.error: return response

        while self.current_token.type in ops:
            op_tok = self.current_token
            response.register(self.get_next_token())
            right = response.register(func())
            if response.error: return response
            left = BinOpNode(left, op_tok, right)

        return response.success(left)


#run function
def run(fn, text):
    # Generate tokens
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    #Generate AST
    parser = Parser(tokens)
    ast = parser.parse()

    return ast.node, ast.error