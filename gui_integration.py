

from parser import CodeAnalyzer

class RealTimeAnalyzer:

    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.last_analysis_result = None
    
    def perform_analysis(self, source_code):
        if not source_code.strip():
            return {
                'success': False,
                'token_info': 'No code to analyze',
                'parse_info': 'No code to analyze',
                'errors': []
            }
        
        # Analizi gerçekleştir
        success = self.analyzer.analyze(source_code)
        
        # Sonuçları hazırla
        result = {
            'success': success,
            'token_info': self.analyzer.get_token_info(),
            'parse_info': self.analyzer.get_parse_info(),
            'errors': self.analyzer.get_errors()
        }
        
        self.last_analysis_result = result
        return result
    
    def get_syntax_highlighting_info(self):
        #Syntax highlighting için token bilgilerini döndür
        if not self.analyzer.tokens:
            return []
        
        highlighting_info = []
        for token in self.analyzer.tokens:
            if token.type.name != 'EOF':
                highlighting_info.append({
                    'type': token.type.name,
                    'value': token.value,
                    'line': token.line,
                    'column': token.column
                })
        
        return highlighting_info


# VS Code Dark Modern temalı syntax renk şeması
SYNTAX_COLORS = {
    'KEYWORD': '#569CD6',  # Mavi (keywords like if, else, return)
    'IDENTIFIER': '#D4D4D4',  # Açık gri (variable names)
    'INTEGER': '#B5CEA8',  # Açık yeşil (numbers)
    'FLOAT': '#B5CEA8',  # Açık yeşil (numbers)
    'STRING': '#CE9178',  # Turuncu-kahve (strings)
    'CHARACTER': '#CE9178',  # Turuncu-kahve (chars)
    'SINGLE_COMMENT': '#6A9955',  # Yeşil (comments)
    'MULTI_COMMENT': '#6A9955',  # Yeşil (comments)
    'PREPROCESSOR': '#C586C0',  # Pembe (preprocessor directives)
    'OPERATOR': '#D4D4D4',  # Açık gri (operators)
    'PUNCTUATION': '#D4D4D4',  # Açık gri (punctuation)
}


def get_token_color(token_type_name):
    # Operator kategorileri
    operators = ['PLUS', 'MINUS', 'MULTIPLY', 'DIVIDE', 'MODULO', 'ASSIGN',
                 'EQUAL', 'NOT_EQUAL', 'LESS', 'LESS_EQUAL', 'GREATER',
                 'GREATER_EQUAL', 'AND', 'OR', 'NOT', 'BITWISE_AND',
                 'BITWISE_OR', 'BITWISE_XOR', 'BITWISE_NOT', 'LEFT_SHIFT',
                 'RIGHT_SHIFT', 'INCREMENT', 'DECREMENT']

    # Punctuation kategorileri
    punctuation = ['SEMICOLON', 'COMMA', 'LEFT_PAREN', 'RIGHT_PAREN',
                   'LEFT_BRACE', 'RIGHT_BRACE', 'LEFT_BRACKET', 'RIGHT_BRACKET',
                   'DOT', 'ARROW']

    if token_type_name in SYNTAX_COLORS:
        return SYNTAX_COLORS[token_type_name]
    elif token_type_name in operators:
        return SYNTAX_COLORS['OPERATOR']
    elif token_type_name in punctuation:
        return SYNTAX_COLORS['PUNCTUATION']
    else:
        return SYNTAX_COLORS['IDENTIFIER']  # Default
