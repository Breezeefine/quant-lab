"""DSL 解析器测试"""

import pytest

from quant_lab.expression.parser import (
    BinOpNode,
    CallNode,
    FeatureNode,
    NumberNode,
    Parser,
    Tokenizer,
    UnaryOpNode,
)


class TestTokenizer:
    def test_simple_feature(self):
        tokens = Tokenizer("$close").tokenize()
        assert tokens[0].type.name == "FEATURE"
        assert tokens[0].value == "close"

    def test_function_call(self):
        tokens = Tokenizer("Mean($close, 20)").tokenize()
        types = [t.type.name for t in tokens if t.type.name != "EOF"]
        assert types == ["IDENT", "LPAREN", "FEATURE", "COMMA", "NUMBER", "RPAREN"]

    def test_nested_call(self):
        tokens = Tokenizer("Rank(Mean($close, 20), 60)").tokenize()
        assert tokens[0].type.name == "IDENT"
        assert tokens[0].value == "Rank"

    def test_arithmetic(self):
        tokens = Tokenizer("$close + 1.5").tokenize()
        types = [t.type.name for t in tokens if t.type.name != "EOF"]
        assert types == ["FEATURE", "PLUS", "NUMBER"]

    def test_comparison(self):
        tokens = Tokenizer("$close > 10").tokenize()
        types = [t.type.name for t in tokens if t.type.name != "EOF"]
        assert types == ["FEATURE", "GT", "NUMBER"]

    def test_negative_number(self):
        tokens = Tokenizer("-$close").tokenize()
        assert tokens[0].type.name == "MINUS"


class TestParser:
    def test_feature(self):
        ast = Parser.parse_expr("$close")
        assert isinstance(ast, FeatureNode)
        assert ast.name == "close"

    def test_number(self):
        ast = Parser.parse_expr("42.5")
        assert isinstance(ast, NumberNode)
        assert ast.value == 42.5

    def test_simple_call(self):
        ast = Parser.parse_expr("Mean($close, 20)")
        assert isinstance(ast, CallNode)
        assert ast.func == "Mean"
        assert len(ast.args) == 2
        assert isinstance(ast.args[0], FeatureNode)
        assert isinstance(ast.args[1], NumberNode)
        assert ast.args[1].value == 20.0

    def test_nested_call(self):
        ast = Parser.parse_expr("Rank(Mean($close, 20), 60)")
        assert isinstance(ast, CallNode)
        assert ast.func == "Rank"
        assert isinstance(ast.args[0], CallNode)
        assert ast.args[0].func == "Mean"

    def test_arithmetic(self):
        ast = Parser.parse_expr("$close + 1")
        assert isinstance(ast, BinOpNode)
        assert ast.op == "+"

    def test_complex_expr(self):
        ast = Parser.parse_expr("Mean($close, 5) - Mean($close, 20)")
        assert isinstance(ast, BinOpNode)
        assert ast.op == "-"
        assert isinstance(ast.left, CallNode)
        assert isinstance(ast.right, CallNode)

    def test_parenthesized(self):
        ast = Parser.parse_expr("($close + $open) / 2")
        assert isinstance(ast, BinOpNode)
        assert ast.op == "/"
        assert isinstance(ast.left, BinOpNode)

    def test_unary_negative(self):
        ast = Parser.parse_expr("-$close")
        assert isinstance(ast, UnaryOpNode)
        assert ast.op == "-"

    def test_comparison(self):
        ast = Parser.parse_expr("$close > 10")
        assert isinstance(ast, BinOpNode)
        assert ast.op == ">"

    def test_error_unexpected_char(self):
        with pytest.raises(SyntaxError):
            Parser.parse_expr("$close & 10")

    def test_error_missing_paren(self):
        with pytest.raises(SyntaxError):
            Parser.parse_expr("Mean($close, 20")
