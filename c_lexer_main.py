
from c_lexer_base import *

class CLexer:
    def __init__(self, source_code):
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.current_token_start = 0
        self.current_token_start_line = 1
        self.current_token_start_column = 1
        self.state = LexerState.START
        self.buffer = ""
        
    def current_char(self):
        if self.position >= len(self.source):
            return None
        return self.source[self.position]
    
    def peek_char(self, offset=1):
        pos = self.position + offset
        if pos >= len(self.source):
            return None
        return self.source[pos]
    
    def advance(self):
        if self.position < len(self.source):
            if self.source[self.position] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.position += 1
    
    def start_token(self):
        self.current_token_start = self.position
        self.current_token_start_line = self.line
        self.current_token_start_column = self.column
        self.buffer = ""
    
    def add_to_buffer(self, char):
        self.buffer += char
    
    def get_buffer_value(self):
        return self.buffer
    
    def create_token(self, token_type, value=None):
        if value is None:
            value = self.buffer
        return Token(token_type, value, self.current_token_start_line, self.current_token_start_column)
    
    def is_keyword(self, identifier):
        return identifier in C_KEYWORDS
    
    def next_token(self):
        while True:
            if self.position >= len(self.source):
                return self.create_token(TokenType.EOF, "")
            
            current_char = self.current_char()
            char_class = char_type(current_char)
            
            # State transition table'dan bir sonraki state'i bul
            transition_key = (self.state, char_class)
            
            # Eğer exact match bulamazsa, daha genel bir match ara
            if transition_key not in TRANSITION_TABLE:
                # Identifier ve integer state'leri için default davranış
                if self.state == LexerState.INTEGER_STATE and char_class not in ['digit', '.']:
                    return self.handle_integer_end()
                elif self.state == LexerState.IDENTIFIER_STATE and char_class not in ['letter', 'digit']:
                    return self.handle_identifier_end()
                elif self.state == LexerState.FLOAT_DIGITS and char_class != 'digit':
                    return self.handle_float_end()
                # String ve char state'leri için default consume
                elif self.state in [LexerState.STRING_STATE, LexerState.CHAR_STATE]:
                    if self.state == LexerState.STRING_STATE and current_char != '"':
                        self.add_to_buffer(current_char)
                        self.advance()
                        continue
                    elif self.state == LexerState.CHAR_STATE and current_char != "'":
                        self.add_to_buffer(current_char)
                        self.advance()
                        continue
                # Comment state'leri için default consume
                elif self.state in [LexerState.SINGLE_COMMENT_STATE, LexerState.MULTI_COMMENT_STATE]:
                    self.add_to_buffer(current_char)
                    self.advance()
                    continue
                # Preprocessor için default consume
                elif self.state == LexerState.PREPROCESSOR_STATE:
                    if char_class not in ['newline']:
                        self.add_to_buffer(current_char)
                        self.advance()
                        continue
                # Single operator states - emit and back
                elif self.state in [LexerState.SLASH_STATE, LexerState.EQUAL_STATE, LexerState.LESS_STATE, 
                                   LexerState.GREATER_STATE, LexerState.NOT_STATE, LexerState.AND_STATE, 
                                   LexerState.OR_STATE, LexerState.PLUS_STATE, LexerState.MINUS_STATE]:
                    return self.handle_single_operator()
                else:
                    return self.create_token(TokenType.ERROR, f"Unexpected character: {current_char}")
            
            next_state, action = TRANSITION_TABLE[transition_key]
            
            # Action'ı uygula
            if action == 'consume':
                if self.state == LexerState.START:
                    self.start_token()
                self.add_to_buffer(current_char)
                self.advance()
                self.state = next_state
                
            elif action == 'skip':
                self.advance()
                # State START'ta kalır
                
            elif action.startswith('emit_'):
                return self.handle_emit_action(action, current_char)
                
            elif action == 'back':
                # Karakteri consume etmeden token emit et
                return self.handle_back_action()
                
            elif action == 'error':
                return self.create_token(TokenType.ERROR, f"Lexical error at {current_char}")
    
    def handle_emit_action(self, action, current_char):
        token_map = {
            'emit_newline': TokenType.NEWLINE,
            'emit_semicolon': TokenType.SEMICOLON,
            'emit_comma': TokenType.COMMA,
            'emit_lparen': TokenType.LEFT_PAREN,
            'emit_rparen': TokenType.RIGHT_PAREN,
            'emit_lbrace': TokenType.LEFT_BRACE,
            'emit_rbrace': TokenType.RIGHT_BRACE,
            'emit_lbracket': TokenType.LEFT_BRACKET,
            'emit_rbracket': TokenType.RIGHT_BRACKET,
            'emit_dot': TokenType.DOT,
            'emit_multiply': TokenType.MULTIPLY,
            'emit_modulo': TokenType.MODULO,
            'emit_xor': TokenType.BITWISE_XOR,
            'emit_not': TokenType.BITWISE_NOT,
            'emit_string': TokenType.STRING,
            'emit_char': TokenType.CHARACTER,
            'emit_comment': TokenType.SINGLE_COMMENT,
            'emit_equal': TokenType.EQUAL,
            'emit_less_equal': TokenType.LESS_EQUAL,
            'emit_left_shift': TokenType.LEFT_SHIFT,
            'emit_greater_equal': TokenType.GREATER_EQUAL,
            'emit_right_shift': TokenType.RIGHT_SHIFT,
            'emit_not_equal': TokenType.NOT_EQUAL,
            'emit_and': TokenType.AND,
            'emit_or': TokenType.OR,
            'emit_increment': TokenType.INCREMENT,
            'emit_decrement': TokenType.DECREMENT,
            'emit_arrow': TokenType.ARROW,
            'emit_preprocessor': TokenType.PREPROCESSOR
        }
        
        if action in ['emit_newline', 'emit_semicolon', 'emit_comma', 'emit_lparen', 'emit_rparen',
                      'emit_lbrace', 'emit_rbrace', 'emit_lbracket', 'emit_rbracket', 'emit_dot',
                      'emit_multiply', 'emit_modulo', 'emit_xor', 'emit_not']:
            # Single character token
            self.start_token()
            self.add_to_buffer(current_char)
            self.advance()
            token = self.create_token(token_map[action])
            self.state = LexerState.START
            return token
        
        elif action in ['emit_string', 'emit_char']:
            # String/char closing quote consume et
            self.add_to_buffer(current_char)
            self.advance()
            token = self.create_token(token_map[action])
            self.state = LexerState.START
            return token
            
        elif action == 'emit_comment':
            if self.state == LexerState.SINGLE_COMMENT_STATE:
                # Newline'ı consume etme, onu ayrı token olarak döndür
                token = self.create_token(TokenType.SINGLE_COMMENT)
                self.state = LexerState.START
                return token
            else:  # Multi comment
                self.add_to_buffer(current_char)  # Closing /
                self.advance()
                token = self.create_token(TokenType.MULTI_COMMENT)
                self.state = LexerState.START
                return token
                
        elif action == 'emit_preprocessor':
            # Newline'ı consume etme
            token = self.create_token(TokenType.PREPROCESSOR)
            self.state = LexerState.START
            return token
            
        else:
            # Multi-character operators
            self.add_to_buffer(current_char)
            self.advance()
            token = self.create_token(token_map[action])
            self.state = LexerState.START
            return token
    
    def handle_integer_end(self):
        token = self.create_token(TokenType.INTEGER)
        self.state = LexerState.START
        return token
    
    def handle_float_end(self):
        token = self.create_token(TokenType.FLOAT)
        self.state = LexerState.START
        return token
    
    def handle_identifier_end(self):
        value = self.get_buffer_value()
        if self.is_keyword(value):
            token = self.create_token(TokenType.KEYWORD)
        else:
            token = self.create_token(TokenType.IDENTIFIER)
        self.state = LexerState.START
        return token
    
    def handle_single_operator(self):
        operator_map = {
            LexerState.SLASH_STATE: TokenType.DIVIDE,
            LexerState.EQUAL_STATE: TokenType.ASSIGN,
            LexerState.LESS_STATE: TokenType.LESS,
            LexerState.GREATER_STATE: TokenType.GREATER,
            LexerState.NOT_STATE: TokenType.NOT,
            LexerState.AND_STATE: TokenType.BITWISE_AND,
            LexerState.OR_STATE: TokenType.BITWISE_OR,
            LexerState.PLUS_STATE: TokenType.PLUS,
            LexerState.MINUS_STATE: TokenType.MINUS
        }
        
        token = self.create_token(operator_map[self.state])
        self.state = LexerState.START
        return token
    
    def tokenize_all(self):
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens