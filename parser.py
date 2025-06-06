
from c_lexer_base import *
from c_lexer_main import CLexer


class ASTNode:
    #Abstract Syntax Tree node
    def __init__(self, node_type, value=None, children=None):
        self.type = node_type
        self.value = value
        self.children = children if children else []
        self.line = None
        self.column = None

    def add_child(self, child):
        if child is not None:  # None child eklemeyi önle
            self.children.append(child)
        return self  # Method chaining için

    def __str__(self):
        return f"{self.type}({self.value})"

    def to_string(self, indent=0):
        result = "  " * indent + str(self) + "\n"
        for child in self.children:
            if isinstance(child, ASTNode):
                result += child.to_string(indent + 1)
            else:
                result += "  " * (indent + 1) + str(child) + "\n"
        return result

class CParser:
    #Recursive Descent Parser

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0
        self.errors = []
        self.max_errors = 50  # Maksimum hata sayısı
        self.recursion_depth = 0
        self.max_recursion_depth = 100  # Maksimum recursion derinliği

    def current_token(self):
        """Şu anki token"""
        if self.current < len(self.tokens):
            return self.tokens[self.current]
        return Token(TokenType.EOF, "", 0, 0)

    def peek_token(self, offset=1):
        pos = self.current + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token(TokenType.EOF, "", 0, 0)

    def advance(self):
        if self.current < len(self.tokens):
            self.current += 1

    def match(self, expected_type):
        if self.current_token().type == expected_type:
            token = self.current_token()
            self.advance()
            return token
        return None

    def expect(self, expected_type):
        token = self.match(expected_type)
        if token is None:
            self.add_error(f"Expected {expected_type}, got {self.current_token().type}")
        return token

    def add_error(self, message):
        if len(self.errors) < self.max_errors:
            current_token = self.current_token()
            self.errors.append(f"{message} at line {current_token.line}, column {current_token.column}")

    def check_recursion_depth(self):
        if self.recursion_depth > self.max_recursion_depth:
            self.add_error("Maximum recursion depth exceeded - possible infinite loop")
            return False
        return True

    def enter_recursion(self):
        self.recursion_depth += 1
        return self.check_recursion_depth()

    def exit_recursion(self):
        self.recursion_depth -= 1

    def skip_to_next_statement(self):
        #bir sonraki statement'a atla hata recovery için
        recovery_tokens = [
            TokenType.SEMICOLON, TokenType.LEFT_BRACE, TokenType.RIGHT_BRACE,
            TokenType.EOF, TokenType.PREPROCESSOR
        ]

        statement_keywords = ['if', 'while', 'for', 'return', 'int', 'float', 'char', 'void', 'double']

        start_pos = self.current

        while (self.current_token().type != TokenType.EOF and
               self.current < len(self.tokens) and
               self.current - start_pos < 100):

            current = self.current_token()

            # Recovery token bulundu
            if current.type in recovery_tokens:
                if current.type == TokenType.SEMICOLON:
                    self.advance()
                break

            # Statement başlatan keyword bulundu
            if (current.type == TokenType.KEYWORD and
                current.value in statement_keywords):
                break

            self.advance()

    def skip_until_balanced(self, open_token, close_token):
        #parantez, bracket, brace
        depth = 1
        start_pos = self.current

        while (self.current_token().type != TokenType.EOF and
               depth > 0 and
               self.current - start_pos < 200):

            current = self.current_token()

            if current.type == open_token:
                depth += 1
            elif current.type == close_token:
                depth -= 1

            self.advance()

    def synchronize(self):
        #major syntax error'dan sonra
        self.advance()  # Geçerli token'ı atla

        while self.current_token().type != TokenType.EOF:
            if self.current_token().type == TokenType.SEMICOLON:
                self.advance()
                return

            # Statement başlatan keyword'ler
            if (self.current_token().type == TokenType.KEYWORD and
                self.current_token().value in ['if', 'while', 'for', 'return', 'int', 'float', 'char', 'void']):
                return

            # Function/class level delimiters
            if self.current_token().type in [TokenType.LEFT_BRACE, TokenType.RIGHT_BRACE]:
                return

            self.advance()

    def parse_program(self):
        program = ASTNode("Program")

        while self.current_token().type != TokenType.EOF:
            # Hata sayısı kontrolü
            if len(self.errors) >= self.max_errors:
                self.add_error("Too many errors, stopping parsing")
                break

            # Whitespace ve comment'ları atla
            if self.current_token().type in [TokenType.WHITESPACE, TokenType.NEWLINE,
                                           TokenType.SINGLE_COMMENT, TokenType.MULTI_COMMENT]:
                self.advance()
                continue

            # Preprocessor directive'leri
            if self.current_token().type == TokenType.PREPROCESSOR:
                node = self.parse_preprocessor()
                if node:
                    program.add_child(node)
                continue

            # Function declaration/definition veya variable declaration
            try:
                declaration = self.parse_declaration()
                if declaration:
                    program.add_child(declaration)
                else:
                    # Hata durumunda synchronize et
                    self.synchronize()
            except Exception as e:
                self.add_error(f"Unexpected error in declaration: {str(e)}")
                self.synchronize()

        return program

    def parse_preprocessor(self):
        token = self.match(TokenType.PREPROCESSOR)
        if token:
            return ASTNode("Preprocessor", token.value)
        return None

    def parse_declaration(self):
        #variable veya function
        # Type specifier bekliyoruz (int, float, char, void, etc.)
        if self.current_token().type != TokenType.KEYWORD:
            return None

        type_token = self.current_token()
        if type_token.value not in ['int', 'float', 'char', 'void', 'double', 'long', 'short', 'signed', 'unsigned']:
            return None

        self.advance()  # Type'ı consume et

        # Identifier bekliyoruz
        if self.current_token().type != TokenType.IDENTIFIER:
            self.add_error(f"Expected identifier after type '{type_token.value}'")
            return None

        identifier = self.current_token()
        self.advance()

        # Function mı variable mı kontrol et
        if self.current_token().type == TokenType.LEFT_PAREN:
            # Function declaration/definition
            return self.parse_function(type_token, identifier)
        else:
            # Variable declaration
            return self.parse_variable_declaration(type_token, identifier)

    def parse_function(self, return_type, name):
        """Function declaration/definition parse et"""
        if not self.enter_recursion():
            return None

        try:
            func_node = ASTNode("Function", name.value)
            func_node.add_child(ASTNode("ReturnType", return_type.value))

            # Parameters
            if not self.expect(TokenType.LEFT_PAREN):
                return func_node

            params = self.parse_parameter_list()
            func_node.add_child(params)

            if not self.expect(TokenType.RIGHT_PAREN):
                # Parantez kapatılmadıysa, kapanana kadar atla
                self.skip_until_balanced(TokenType.LEFT_PAREN, TokenType.RIGHT_PAREN)

            # Function body veya sadece declaration
            if self.current_token().type == TokenType.LEFT_BRACE:
                # Function definition
                body = self.parse_compound_statement()
                if body:
                    func_node.add_child(body)
            else:
                # Function declaration
                self.expect(TokenType.SEMICOLON)

            return func_node
        finally:
            self.exit_recursion()

    def parse_parameter_list(self):
        """Parameter listesi parse et"""
        params = ASTNode("Parameters")

        if self.current_token().type == TokenType.RIGHT_PAREN:
            return params  # Boş parameter listesi

        while True:
            # Güvenlik kontrolü
            if self.current_token().type in [TokenType.EOF, TokenType.RIGHT_PAREN]:
                break

            # Parameter: type identifier
            if self.current_token().type == TokenType.KEYWORD:
                type_token = self.current_token()
                self.advance()

                if self.current_token().type == TokenType.IDENTIFIER:
                    param_name = self.current_token()
                    self.advance()

                    param = ASTNode("Parameter", param_name.value)
                    param.add_child(ASTNode("Type", type_token.value))
                    params.add_child(param)
                else:
                    self.add_error("Expected parameter name")
                    break
            else:
                self.add_error("Expected parameter type")
                break

            # Comma ile ayrılmış parametreler
            if self.current_token().type == TokenType.COMMA:
                self.advance()
            else:
                break

        return params

    def parse_variable_declaration(self, type_token, identifier):
        """Variable declaration parse et"""
        var_node = ASTNode("VariableDeclaration", identifier.value)
        var_node.add_child(ASTNode("Type", type_token.value))

        # Array declaration kontrol et
        if self.current_token().type == TokenType.LEFT_BRACKET:
            self.advance()
            # Array size (şimdilik basit integer)
            if self.current_token().type == TokenType.INTEGER:
                size = self.current_token()
                var_node.add_child(ASTNode("ArraySize", size.value))
                self.advance()

            if not self.expect(TokenType.RIGHT_BRACKET):
                self.skip_until_balanced(TokenType.LEFT_BRACKET, TokenType.RIGHT_BRACKET)

        # Initialization
        if self.current_token().type == TokenType.ASSIGN:
            self.advance()
            init_expr = self.parse_expression()
            if init_expr:
                var_node.add_child(ASTNode("Initializer").add_child(init_expr))

        self.expect(TokenType.SEMICOLON)
        return var_node

    def parse_compound_statement(self):
        """Compound statement (block) parse et"""
        if not self.enter_recursion():
            return None

        try:
            if not self.expect(TokenType.LEFT_BRACE):
                return None

            block = ASTNode("Block")

            while (self.current_token().type != TokenType.RIGHT_BRACE and
                   self.current_token().type != TokenType.EOF):

                # Whitespace ve comment'ları atla
                if self.current_token().type in [TokenType.WHITESPACE, TokenType.NEWLINE,
                                                 TokenType.SINGLE_COMMENT, TokenType.MULTI_COMMENT]:
                    self.advance()
                    continue

                stmt = self.parse_statement()
                if stmt:
                    block.add_child(stmt)
                else:
                    self.skip_to_next_statement()

            self.expect(TokenType.RIGHT_BRACE)
            return block
        finally:
            self.exit_recursion()

    def parse_statement(self):
        """Statement parse et"""
        if not self.enter_recursion():
            return None

        try:
            token = self.current_token()

            # Control flow statements
            if token.type == TokenType.KEYWORD:
                if token.value == "if":
                    return self.parse_if_statement()
                elif token.value == "while":
                    return self.parse_while_statement()
                elif token.value == "for":
                    return self.parse_for_statement()
                elif token.value == "return":
                    return self.parse_return_statement()
                elif token.value in ['int', 'float', 'char', 'void', 'double']:
                    # Local variable declaration
                    return self.parse_declaration()

            # Compound statement
            if token.type == TokenType.LEFT_BRACE:
                return self.parse_compound_statement()

            # Expression statement
            expr = self.parse_expression()
            if expr:
                self.expect(TokenType.SEMICOLON)
                return ASTNode("ExpressionStatement").add_child(expr)

            return None
        finally:
            self.exit_recursion()

    def parse_if_statement(self):
        """If statement parse et"""
        self.expect(TokenType.KEYWORD)  # 'if'

        if not self.expect(TokenType.LEFT_PAREN):
            return None

        condition = self.parse_expression()
        if_node = ASTNode("IfStatement")
        if_node.add_child(ASTNode("Condition").add_child(condition))

        if not self.expect(TokenType.RIGHT_PAREN):
            self.skip_until_balanced(TokenType.LEFT_PAREN, TokenType.RIGHT_PAREN)

        then_stmt = self.parse_statement()
        if then_stmt:
            if_node.add_child(ASTNode("ThenStatement").add_child(then_stmt))

        # Else clause
        if (self.current_token().type == TokenType.KEYWORD and
            self.current_token().value == "else"):
            self.advance()
            else_stmt = self.parse_statement()
            if else_stmt:
                if_node.add_child(ASTNode("ElseStatement").add_child(else_stmt))

        return if_node

    def parse_while_statement(self):
        """While statement parse et"""
        self.expect(TokenType.KEYWORD)  # 'while'

        if not self.expect(TokenType.LEFT_PAREN):
            return None

        condition = self.parse_expression()
        while_node = ASTNode("WhileStatement")
        if condition:
            while_node.add_child(ASTNode("Condition").add_child(condition))

        if not self.expect(TokenType.RIGHT_PAREN):
            self.skip_until_balanced(TokenType.LEFT_PAREN, TokenType.RIGHT_PAREN)

        body = self.parse_statement()
        if body:
            while_node.add_child(ASTNode("Body").add_child(body))

        return while_node

    def parse_for_statement(self):
        """For statement parse et"""
        self.expect(TokenType.KEYWORD)  # 'for'

        if not self.expect(TokenType.LEFT_PAREN):
            return None

        for_node = ASTNode("ForStatement")

        # Initialization (optional)
        if self.current_token().type != TokenType.SEMICOLON:
            if (self.current_token().type == TokenType.KEYWORD and
                self.current_token().value in ['int', 'float', 'char', 'void', 'double']):
                # Variable declaration
                init_stmt = self.parse_declaration()
            else:
                # Expression statement
                init_expr = self.parse_expression()
                if init_expr:
                    init_stmt = ASTNode("ExpressionStatement").add_child(init_expr)
                else:
                    init_stmt = None
                self.expect(TokenType.SEMICOLON)

            if init_stmt:
                for_node.add_child(ASTNode("Initialization").add_child(init_stmt))
        else:
            self.expect(TokenType.SEMICOLON)
            for_node.add_child(ASTNode("Initialization"))

        # Condition (optional)
        if self.current_token().type != TokenType.SEMICOLON:
            condition = self.parse_expression()
            if condition:
                for_node.add_child(ASTNode("Condition").add_child(condition))
        else:
            for_node.add_child(ASTNode("Condition"))

        self.expect(TokenType.SEMICOLON)

        # Increment/Update (optional)
        if self.current_token().type != TokenType.RIGHT_PAREN:
            increment = self.parse_expression()
            if increment:
                for_node.add_child(ASTNode("Increment").add_child(increment))
        else:
            for_node.add_child(ASTNode("Increment"))

        if not self.expect(TokenType.RIGHT_PAREN):
            self.skip_until_balanced(TokenType.LEFT_PAREN, TokenType.RIGHT_PAREN)

        # Body
        body = self.parse_statement()
        if body:
            for_node.add_child(ASTNode("Body").add_child(body))

        return for_node

    def parse_return_statement(self):
        """Return statement parse et"""
        self.expect(TokenType.KEYWORD)  # 'return'

        return_node = ASTNode("ReturnStatement")

        # Optional return value
        if self.current_token().type != TokenType.SEMICOLON:
            expr = self.parse_expression()
            if expr:
                return_node.add_child(expr)

        self.expect(TokenType.SEMICOLON)
        return return_node

    def parse_expression(self):
        """Expression parse et"""
        if not self.enter_recursion():
            return None

        try:
            return self.parse_assignment_expression()
        finally:
            self.exit_recursion()

    def parse_assignment_expression(self):
        """Assignment expression parse et"""
        left = self.parse_logical_or_expression()

        if self.current_token().type == TokenType.ASSIGN:
            op = self.current_token()
            self.advance()
            right = self.parse_assignment_expression()

            if left and right:
                assign_node = ASTNode("Assignment", op.value)
                assign_node.add_child(left)
                assign_node.add_child(right)
                return assign_node

        return left

    def parse_logical_or_expression(self):
        """Logical OR expression parse et"""
        left = self.parse_logical_and_expression()

        while self.current_token().type == TokenType.OR:
            op = self.current_token()
            self.advance()
            right = self.parse_logical_and_expression()

            if left and right:
                binary_node = ASTNode("BinaryOp", op.value)
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def parse_logical_and_expression(self):
        """Logical AND expression parse et"""
        left = self.parse_equality_expression()

        while self.current_token().type == TokenType.AND:
            op = self.current_token()
            self.advance()
            right = self.parse_equality_expression()

            if left and right:
                binary_node = ASTNode("BinaryOp", op.value)
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def parse_equality_expression(self):
        """Equality expression parse et"""
        left = self.parse_relational_expression()

        while self.current_token().type in [TokenType.EQUAL, TokenType.NOT_EQUAL]:
            op = self.current_token()
            self.advance()
            right = self.parse_relational_expression()

            if left and right:
                binary_node = ASTNode("BinaryOp", op.value)
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def parse_relational_expression(self):
        """Relational expression parse et"""
        left = self.parse_additive_expression()

        while self.current_token().type in [TokenType.LESS, TokenType.LESS_EQUAL,
                                          TokenType.GREATER, TokenType.GREATER_EQUAL]:
            op = self.current_token()
            self.advance()
            right = self.parse_additive_expression()

            if left and right:
                binary_node = ASTNode("BinaryOp", op.value)
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def parse_additive_expression(self):
        """Additive expression parse et"""
        left = self.parse_multiplicative_expression()

        while self.current_token().type in [TokenType.PLUS, TokenType.MINUS]:
            op = self.current_token()
            self.advance()
            right = self.parse_multiplicative_expression()

            if left and right:
                binary_node = ASTNode("BinaryOp", op.value)
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def parse_multiplicative_expression(self):
        """Multiplicative expression parse et"""
        left = self.parse_unary_expression()

        while self.current_token().type in [TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO]:
            op = self.current_token()
            self.advance()
            right = self.parse_unary_expression()

            if left and right:
                binary_node = ASTNode("BinaryOp", op.value)
                binary_node.add_child(left)
                binary_node.add_child(right)
                left = binary_node
            else:
                break

        return left

    def parse_unary_expression(self):
        """Unary expression parse et"""
        if self.current_token().type in [TokenType.NOT, TokenType.MINUS, TokenType.PLUS]:
            op = self.current_token()
            self.advance()
            expr = self.parse_unary_expression()

            if expr:
                unary_node = ASTNode("UnaryOp", op.value)
                unary_node.add_child(expr)
                return unary_node

        return self.parse_postfix_expression()

    def parse_postfix_expression(self):
        """Postfix expression parse et"""
        left = self.parse_primary_expression()
        if not left:
            return None

        iteration_count = 0
        max_iterations = 50  # Sonsuz döngü koruması

        while iteration_count < max_iterations:
            iteration_count += 1

            if self.current_token().type == TokenType.LEFT_PAREN:
                # Function call
                self.advance()
                args = self.parse_argument_list()
                if not self.expect(TokenType.RIGHT_PAREN):
                    self.skip_until_balanced(TokenType.LEFT_PAREN, TokenType.RIGHT_PAREN)

                call_node = ASTNode("FunctionCall")
                call_node.add_child(left)
                if args:
                    call_node.add_child(args)
                left = call_node

            elif self.current_token().type == TokenType.LEFT_BRACKET:
                # Array access
                self.advance()
                index = self.parse_expression()
                if not self.expect(TokenType.RIGHT_BRACKET):
                    self.skip_until_balanced(TokenType.LEFT_BRACKET, TokenType.RIGHT_BRACKET)

                if index:
                    array_node = ASTNode("ArrayAccess")
                    array_node.add_child(left)
                    array_node.add_child(index)
                    left = array_node

            else:
                break

        if iteration_count >= max_iterations:
            self.add_error("Maximum iterations exceeded in postfix expression")

        return left

    def parse_argument_list(self):
        """Argument listesi parse et"""
        args = ASTNode("Arguments")

        if self.current_token().type == TokenType.RIGHT_PAREN:
            return args  # Boş argument listesi

        arg_count = 0
        max_args = 50  # Sonsuz döngü koruması

        while arg_count < max_args and self.current_token().type != TokenType.RIGHT_PAREN:
            arg_count += 1

            expr = self.parse_expression()
            if expr:
                args.add_child(expr)

            if self.current_token().type == TokenType.COMMA:
                self.advance()
            else:
                break

        return args

    def parse_primary_expression(self):
        """Primary expression parse et"""
        token = self.current_token()

        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return ASTNode("Identifier", token.value)

        elif token.type == TokenType.INTEGER:
            self.advance()
            return ASTNode("Integer", token.value)

        elif token.type == TokenType.FLOAT:
            self.advance()
            return ASTNode("Float", token.value)

        elif token.type == TokenType.CHARACTER:
            self.advance()
            return ASTNode("Character", token.value)

        elif token.type == TokenType.STRING:
            self.advance()
            return ASTNode("String", token.value)

        elif token.type == TokenType.LEFT_PAREN:
            self.advance()
            expr = self.parse_expression()
            if not self.expect(TokenType.RIGHT_PAREN):
                self.skip_until_balanced(TokenType.LEFT_PAREN, TokenType.RIGHT_PAREN)
            return expr

        else:
            # Unexpected token için hata ver ama None dönme
            if token.type != TokenType.EOF and token.type not in [TokenType.SEMICOLON,
                                                                  TokenType.RIGHT_PAREN,
                                                                  TokenType.RIGHT_BRACE]:
                self.add_error(f"Unexpected token {token.type}")
                self.advance()  # Skip the problematic token
            return None


class CodeAnalyzer:
    """Ana analiz sınıfı"""

    def __init__(self):
        self.lexer = None
        self.parser = None
        self.tokens = []
        self.ast = None
        self.errors = []

    def analyze(self, source_code):
        """Kodu analiz et"""
        self.errors = []

        try:
            # Lexical Analysis
            self.lexer = CLexer(source_code)
            self.tokens = self.lexer.tokenize_all()

            # Syntax Analysis
            self.parser = CParser(self.tokens)
            self.ast = self.parser.parse_program()
            self.errors.extend(self.parser.errors)

            return True
        except Exception as e:
            self.errors.append(f"Analysis error: {str(e)}")
            return False

    def get_token_info(self):
        """Token bilgilerini döndür"""
        if not self.tokens:
            return "No tokens available"

        info = f"Total tokens: {len(self.tokens)}\n\n"

        # Token type counts
        token_counts = {}
        for token in self.tokens:
            if token.type != TokenType.EOF:
                token_counts[token.type] = token_counts.get(token.type, 0) + 1

        info += "Token distribution:\n"
        for token_type, count in sorted(token_counts.items(), key=lambda x: x[1], reverse=True):
            info += f"  {token_type.name}: {count}\n"

        info += "\n---TOKENS---:\n"
        for token in self.tokens:
            if token.type != TokenType.EOF:
                info += f"{token.type.name}: {token.value}\n"

        return info

    def get_parse_info(self):
        """Parse bilgilerini döndür"""
        if not self.ast:
            return "No parse tree available"

        info = f"Parse tree structure:\n"
        info += self.ast.to_string()

        if self.errors:
            info += f"\nSyntax errors ({len(self.errors)}):\n"
            for error in self.errors:
                info += f"  - {error}\n"
        else:
            info += "\nNo syntax errors found.\n"

        return info

    def get_errors(self):
        """Hataları döndür"""
        return self.errors

    def is_valid_syntax(self):
        """Syntax'ın geçerli olup olmadığını kontrol et"""
        return len(self.errors) == 0