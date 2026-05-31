"""DSL 解析器 — 将表达式字符串解析为 AST

语法：
    expr     → comparison
    comparison → add ((">" | "<" | ">=" | "<=" | "==" | "!=") add)*
    add      → mul (("+" | "-") mul)*
    mul      → unary (("*" | "/" | "%") unary)*
    unary    → "-" unary | call
    call     → IDENT "(" args ")" | atom
    args     → expr ("," expr)*
    atom     → NUMBER | "$" IDENT | "(" expr ")"

示例：
    Mean($close, 20)
    Rank(Mean($close, 20), 60)
    $close / $open - 1
    Mean($close, 5) - Mean($close, 20)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Union


# --- AST 节点定义 ---

@dataclass(frozen=True)
class FeatureNode:
    """特征引用，如 $close"""
    name: str


@dataclass(frozen=True)
class NumberNode:
    """数值常量"""
    value: float


@dataclass(frozen=True)
class CallNode:
    """函数调用，如 Mean($close, 20)"""
    func: str
    args: tuple[ASTNode, ...]


@dataclass(frozen=True)
class BinOpNode:
    """二元运算"""
    op: str
    left: ASTNode
    right: ASTNode


@dataclass(frozen=True)
class UnaryOpNode:
    """一元运算（取负）"""
    op: str
    operand: ASTNode


ASTNode = Union[FeatureNode, NumberNode, CallNode, BinOpNode, UnaryOpNode]


# --- Token 类型 ---

class TokenType(Enum):
    NUMBER = auto()
    IDENT = auto()
    FEATURE = auto()   # $close 等
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    GT = auto()
    LT = auto()
    GTE = auto()
    LTE = auto()
    EQ = auto()
    NEQ = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    pos: int


# --- 词法分析器 ---

class Tokenizer:
    """将表达式字符串拆分为 token 流"""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def _skip_whitespace(self):
        while self.pos < len(self.text) and self.text[self.pos].isspace():
            self.pos += 1

    def _read_number(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            self.pos += 1
        return Token(TokenType.NUMBER, self.text[start:self.pos], start)

    def _read_ident(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return Token(TokenType.IDENT, self.text[start:self.pos], start)

    def _read_feature(self) -> Token:
        """读取 $name 特征引用"""
        start = self.pos
        self.pos += 1  # 跳过 $
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] == '_'):
            self.pos += 1
        return Token(TokenType.FEATURE, self.text[start + 1:self.pos], start)

    def tokenize(self) -> list[Token]:
        tokens = []
        while self.pos < len(self.text):
            self._skip_whitespace()
            if self.pos >= len(self.text):
                break

            ch = self.text[self.pos]

            if ch.isdigit() or (ch == '.' and self.pos + 1 < len(self.text) and self.text[self.pos + 1].isdigit()):
                tokens.append(self._read_number())
            elif ch == '$':
                tokens.append(self._read_feature())
            elif ch.isalpha() or ch == '_':
                tokens.append(self._read_ident())
            elif ch == '+':
                tokens.append(Token(TokenType.PLUS, '+', self.pos)); self.pos += 1
            elif ch == '-':
                tokens.append(Token(TokenType.MINUS, '-', self.pos)); self.pos += 1
            elif ch == '*':
                tokens.append(Token(TokenType.STAR, '*', self.pos)); self.pos += 1
            elif ch == '/':
                tokens.append(Token(TokenType.SLASH, '/', self.pos)); self.pos += 1
            elif ch == '%':
                tokens.append(Token(TokenType.PERCENT, '%', self.pos)); self.pos += 1
            elif ch == '(':
                tokens.append(Token(TokenType.LPAREN, '(', self.pos)); self.pos += 1
            elif ch == ')':
                tokens.append(Token(TokenType.RPAREN, ')', self.pos)); self.pos += 1
            elif ch == ',':
                tokens.append(Token(TokenType.COMMA, ',', self.pos)); self.pos += 1
            elif ch == '>' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                tokens.append(Token(TokenType.GTE, '>=', self.pos)); self.pos += 2
            elif ch == '>':
                tokens.append(Token(TokenType.GT, '>', self.pos)); self.pos += 1
            elif ch == '<' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                tokens.append(Token(TokenType.LTE, '<=', self.pos)); self.pos += 2
            elif ch == '<':
                tokens.append(Token(TokenType.LT, '<', self.pos)); self.pos += 1
            elif ch == '!' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                tokens.append(Token(TokenType.NEQ, '!=', self.pos)); self.pos += 2
            elif ch == '=' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '=':
                tokens.append(Token(TokenType.EQ, '==', self.pos)); self.pos += 2
            else:
                raise SyntaxError(f"Unexpected character '{ch}' at position {self.pos}")

        tokens.append(Token(TokenType.EOF, '', self.pos))
        return tokens


# --- 语法分析器 ---

class Parser:
    """递归下降解析器，将 token 流解析为 AST"""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _eat(self, expected: TokenType) -> Token:
        token = self._current()
        if token.type != expected:
            raise SyntaxError(f"Expected {expected.name}, got {token.type.name} '{token.value}' at position {token.pos}")
        self.pos += 1
        return token

    def _match(self, *types: TokenType) -> Token | None:
        if self._current().type in types:
            token = self._current()
            self.pos += 1
            return token
        return None

    def parse(self) -> ASTNode:
        """解析表达式，返回 AST 根节点"""
        node = self._comparison()
        if self._current().type != TokenType.EOF:
            raise SyntaxError(f"Unexpected token '{self._current().value}' at position {self._current().pos}")
        return node

    def _comparison(self) -> ASTNode:
        left = self._add()
        op_token = self._match(TokenType.GT, TokenType.LT, TokenType.GTE, TokenType.LTE, TokenType.EQ, TokenType.NEQ)
        if op_token:
            right = self._add()
            return BinOpNode(op=op_token.value, left=left, right=right)
        return left

    def _add(self) -> ASTNode:
        left = self._mul()
        while (op_token := self._match(TokenType.PLUS, TokenType.MINUS)):
            right = self._mul()
            left = BinOpNode(op=op_token.value, left=left, right=right)
        return left

    def _mul(self) -> ASTNode:
        left = self._unary()
        while (op_token := self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT)):
            right = self._unary()
            left = BinOpNode(op=op_token.value, left=left, right=right)
        return left

    def _unary(self) -> ASTNode:
        if self._match(TokenType.MINUS):
            operand = self._unary()
            return UnaryOpNode(op='-', operand=operand)
        return self._call()

    def _call(self) -> ASTNode:
        if self._current().type == TokenType.IDENT and self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == TokenType.LPAREN:
            name = self._eat(TokenType.IDENT).value
            self._eat(TokenType.LPAREN)
            args = self._args()
            self._eat(TokenType.RPAREN)
            return CallNode(func=name, args=tuple(args))
        return self._atom()

    def _args(self) -> list[ASTNode]:
        args = [self._comparison()]
        while self._match(TokenType.COMMA):
            args.append(self._comparison())
        return args

    def _atom(self) -> ASTNode:
        if self._current().type == TokenType.NUMBER:
            return NumberNode(value=float(self._eat(TokenType.NUMBER).value))
        if self._current().type == TokenType.FEATURE:
            return FeatureNode(name=self._eat(TokenType.FEATURE).value)
        if self._current().type == TokenType.LPAREN:
            self._eat(TokenType.LPAREN)
            node = self._comparison()
            self._eat(TokenType.RPAREN)
            return node
        raise SyntaxError(f"Unexpected token '{self._current().value}' at position {self._current().pos}")

    @classmethod
    def parse_expr(cls, text: str) -> ASTNode:
        """便捷方法：直接从字符串解析为 AST"""
        tokens = Tokenizer(text).tokenize()
        return cls(tokens).parse()
