
# lexer için gerekli olan token tipleri, state'ler ve transition table'lar

from enum import Enum, auto


class TokenType(Enum):
    # Literals
    INTEGER = auto()
    FLOAT = auto()
    CHARACTER = auto()
    STRING = auto()
    
    # Identifiers and Keywords
    IDENTIFIER = auto()
    KEYWORD = auto()
    
    # Operators
    PLUS = auto()           # +
    MINUS = auto()          # -
    MULTIPLY = auto()       # *
    DIVIDE = auto()         # /
    MODULO = auto()         # %
    ASSIGN = auto()         # =
    EQUAL = auto()          # ==
    NOT_EQUAL = auto()      # !=
    LESS = auto()           # <
    LESS_EQUAL = auto()     # <=
    GREATER = auto()        # >
    GREATER_EQUAL = auto()  # >=
    AND = auto()            # &&
    OR = auto()             # ||
    NOT = auto()            # !
    BITWISE_AND = auto()    # &
    BITWISE_OR = auto()     # |
    BITWISE_XOR = auto()    # ^
    BITWISE_NOT = auto()    # ~
    LEFT_SHIFT = auto()     # <<
    RIGHT_SHIFT = auto()    # >>
    INCREMENT = auto()      # ++
    DECREMENT = auto()      # --
    
    # Punctuation
    SEMICOLON = auto()      # ;
    COMMA = auto()          # ,
    LEFT_PAREN = auto()     # (
    RIGHT_PAREN = auto()    # )
    LEFT_BRACE = auto()     # {
    RIGHT_BRACE = auto()    # }
    LEFT_BRACKET = auto()   # [
    RIGHT_BRACKET = auto()  # ]
    DOT = auto()            # .
    ARROW = auto()          # ->
    
    # Preprocessor
    PREPROCESSOR = auto()   # #include, #define, etc.
    
    # Comments
    SINGLE_COMMENT = auto() # //
    MULTI_COMMENT = auto()  # /* */
    
    # Special
    WHITESPACE = auto()
    NEWLINE = auto()
    EOF = auto()
    ERROR = auto()

class LexerState(Enum):
    START = auto()
    
    # Number states
    INTEGER_STATE = auto()
    FLOAT_DOT = auto()
    FLOAT_DIGITS = auto()
    
    # Identifier/Keyword states
    IDENTIFIER_STATE = auto()
    
    # String states
    STRING_STATE = auto()
    STRING_ESCAPE = auto()
    
    # Character states
    CHAR_STATE = auto()
    CHAR_ESCAPE = auto()
    
    # Comment states
    SLASH_STATE = auto()
    SINGLE_COMMENT_STATE = auto()
    MULTI_COMMENT_STATE = auto()
    MULTI_COMMENT_END = auto()
    
    # Operator states
    EQUAL_STATE = auto()        # = veya ==
    LESS_STATE = auto()         # < veya <= veya <<
    GREATER_STATE = auto()      # > veya >= veya >>
    NOT_STATE = auto()          # ! veya !=
    AND_STATE = auto()          # & veya &&
    OR_STATE = auto()           # | veya ||
    PLUS_STATE = auto()         # + veya ++
    MINUS_STATE = auto()        # - veya -- veya ->
    
    # Preprocessor states
    PREPROCESSOR_STATE = auto()
    
    # Final states
    ACCEPT = auto()
    ERROR = auto()

# C Keywords
C_KEYWORDS = {
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if',
    'int', 'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
}

class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __str__(self):
        return f"Token({self.type}, '{self.value}', {self.line}:{self.column})"
    
    def __repr__(self):
        return self.__str__()

# State Transition Table
# Format: {(current_state, input_char_type): (next_state, action)}
# Actions: 'consume', 'emit', 'back', 'error'

def char_type(ch):
    if ch.isdigit():
        return 'digit'
    elif ch.isalpha() or ch == '_':
        return 'letter'
    elif ch.isspace():
        if ch == '\n':
            return 'newline'
        return 'whitespace'
    else:
        return ch

# State Transition Table
TRANSITION_TABLE = {
    # START state transitions
    (LexerState.START, 'digit'): (LexerState.INTEGER_STATE, 'consume'),
    (LexerState.START, 'letter'): (LexerState.IDENTIFIER_STATE, 'consume'),
    (LexerState.START, '"'): (LexerState.STRING_STATE, 'consume'),
    (LexerState.START, "'"): (LexerState.CHAR_STATE, 'consume'),
    (LexerState.START, '/'): (LexerState.SLASH_STATE, 'consume'),
    (LexerState.START, '='): (LexerState.EQUAL_STATE, 'consume'),
    (LexerState.START, '<'): (LexerState.LESS_STATE, 'consume'),
    (LexerState.START, '>'): (LexerState.GREATER_STATE, 'consume'),
    (LexerState.START, '!'): (LexerState.NOT_STATE, 'consume'),
    (LexerState.START, '&'): (LexerState.AND_STATE, 'consume'),
    (LexerState.START, '|'): (LexerState.OR_STATE, 'consume'),
    (LexerState.START, '+'): (LexerState.PLUS_STATE, 'consume'),
    (LexerState.START, '-'): (LexerState.MINUS_STATE, 'consume'),
    (LexerState.START, '#'): (LexerState.PREPROCESSOR_STATE, 'consume'),
    (LexerState.START, 'whitespace'): (LexerState.START, 'skip'),
    (LexerState.START, 'newline'): (LexerState.ACCEPT, 'emit_newline'),
    
    # Single character tokens
    (LexerState.START, ';'): (LexerState.ACCEPT, 'emit_semicolon'),
    (LexerState.START, ','): (LexerState.ACCEPT, 'emit_comma'),
    (LexerState.START, '('): (LexerState.ACCEPT, 'emit_lparen'),
    (LexerState.START, ')'): (LexerState.ACCEPT, 'emit_rparen'),
    (LexerState.START, '{'): (LexerState.ACCEPT, 'emit_lbrace'),
    (LexerState.START, '}'): (LexerState.ACCEPT, 'emit_rbrace'),
    (LexerState.START, '['): (LexerState.ACCEPT, 'emit_lbracket'),
    (LexerState.START, ']'): (LexerState.ACCEPT, 'emit_rbracket'),
    (LexerState.START, '.'): (LexerState.ACCEPT, 'emit_dot'),
    (LexerState.START, '*'): (LexerState.ACCEPT, 'emit_multiply'),
    (LexerState.START, '%'): (LexerState.ACCEPT, 'emit_modulo'),
    (LexerState.START, '^'): (LexerState.ACCEPT, 'emit_xor'),
    (LexerState.START, '~'): (LexerState.ACCEPT, 'emit_not'),
    
    # INTEGER_STATE transitions
    (LexerState.INTEGER_STATE, 'digit'): (LexerState.INTEGER_STATE, 'consume'),
    (LexerState.INTEGER_STATE, '.'): (LexerState.FLOAT_DOT, 'consume'),
    # Diğer karakterler için INTEGER token emit et ve geri git
    
    # FLOAT states
    (LexerState.FLOAT_DOT, 'digit'): (LexerState.FLOAT_DIGITS, 'consume'),
    (LexerState.FLOAT_DIGITS, 'digit'): (LexerState.FLOAT_DIGITS, 'consume'),
    
    # IDENTIFIER_STATE transitions
    (LexerState.IDENTIFIER_STATE, 'letter'): (LexerState.IDENTIFIER_STATE, 'consume'),
    (LexerState.IDENTIFIER_STATE, 'digit'): (LexerState.IDENTIFIER_STATE, 'consume'),
    
    # STRING_STATE transitions
    (LexerState.STRING_STATE, '"'): (LexerState.ACCEPT, 'emit_string'),
    (LexerState.STRING_STATE, '\\'): (LexerState.STRING_ESCAPE, 'consume'),
    
    # CHAR_STATE transitions
    (LexerState.CHAR_STATE, "'"): (LexerState.ACCEPT, 'emit_char'),
    (LexerState.CHAR_STATE, '\\'): (LexerState.CHAR_ESCAPE, 'consume'),
    
    # Comment states
    (LexerState.SLASH_STATE, '/'): (LexerState.SINGLE_COMMENT_STATE, 'consume'),
    (LexerState.SLASH_STATE, '*'): (LexerState.MULTI_COMMENT_STATE, 'consume'),
    (LexerState.SINGLE_COMMENT_STATE, 'newline'): (LexerState.ACCEPT, 'emit_comment'),
    (LexerState.MULTI_COMMENT_STATE, '*'): (LexerState.MULTI_COMMENT_END, 'consume'),
    (LexerState.MULTI_COMMENT_END, '/'): (LexerState.ACCEPT, 'emit_comment'),
    (LexerState.MULTI_COMMENT_END, '*'): (LexerState.MULTI_COMMENT_END, 'consume'),
    
    # Operator states
    (LexerState.EQUAL_STATE, '='): (LexerState.ACCEPT, 'emit_equal'),
    (LexerState.LESS_STATE, '='): (LexerState.ACCEPT, 'emit_less_equal'),
    (LexerState.LESS_STATE, '<'): (LexerState.ACCEPT, 'emit_left_shift'),
    (LexerState.GREATER_STATE, '='): (LexerState.ACCEPT, 'emit_greater_equal'),
    (LexerState.GREATER_STATE, '>'): (LexerState.ACCEPT, 'emit_right_shift'),
    (LexerState.NOT_STATE, '='): (LexerState.ACCEPT, 'emit_not_equal'),
    (LexerState.AND_STATE, '&'): (LexerState.ACCEPT, 'emit_and'),
    (LexerState.OR_STATE, '|'): (LexerState.ACCEPT, 'emit_or'),
    (LexerState.PLUS_STATE, '+'): (LexerState.ACCEPT, 'emit_increment'),
    (LexerState.MINUS_STATE, '-'): (LexerState.ACCEPT, 'emit_decrement'),
    (LexerState.MINUS_STATE, '>'): (LexerState.ACCEPT, 'emit_arrow'),
    
    # PREPROCESSOR_STATE transitions
    (LexerState.PREPROCESSOR_STATE, 'letter'): (LexerState.PREPROCESSOR_STATE, 'consume'),
    (LexerState.PREPROCESSOR_STATE, 'newline'): (LexerState.ACCEPT, 'emit_preprocessor'),
}