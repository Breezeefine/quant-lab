"""AST → Polars 编译器

将 AST 编译为 Polars 表达式，可在 DataFrame 上执行。
"""

from __future__ import annotations

import polars as pl

from .operators import REGISTRY
from .parser import ASTNode, BinOpNode, CallNode, FeatureNode, NumberNode, UnaryOpNode


class CompilerError(Exception):
    """编译错误"""
    pass


class Compiler:
    """AST → Polars 表达式编译器"""

    def compile(self, node: ASTNode) -> pl.Expr:
        """将 AST 节点编译为 Polars 表达式"""
        return self._compile_node(node)

    def _compile_node(self, node: ASTNode) -> pl.Expr:
        if isinstance(node, FeatureNode):
            return pl.col(node.name)

        if isinstance(node, NumberNode):
            return pl.lit(node.value)

        if isinstance(node, BinOpNode):
            return self._compile_binop(node)

        if isinstance(node, UnaryOpNode):
            return self._compile_unaryop(node)

        if isinstance(node, CallNode):
            return self._compile_call(node)

        raise CompilerError(f"Unknown node type: {type(node).__name__}")

    def _compile_binop(self, node: BinOpNode) -> pl.Expr:
        left = self._compile_node(node.left)
        right = self._compile_node(node.right)

        ops = {
            '+': lambda l, r: l + r,
            '-': lambda l, r: l - r,
            '*': lambda l, r: l * r,
            '/': lambda l, r: l / r,
            '%': lambda l, r: l % r,
            '>': lambda l, r: l > r,
            '<': lambda l, r: l < r,
            '>=': lambda l, r: l >= r,
            '<=': lambda l, r: l <= r,
            '==': lambda l, r: l == r,
            '!=': lambda l, r: l != r,
        }

        if node.op not in ops:
            raise CompilerError(f"Unknown operator: {node.op}")

        return ops[node.op](left, right)

    def _compile_unaryop(self, node: UnaryOpNode) -> pl.Expr:
        operand = self._compile_node(node.operand)
        if node.op == '-':
            return -operand
        raise CompilerError(f"Unknown unary operator: {node.op}")

    def _compile_call(self, node: CallNode) -> pl.Expr:
        func_name = node.func
        if func_name not in REGISTRY:
            raise CompilerError(f"Unknown function: {func_name}")

        func = REGISTRY[func_name]
        compiled_args = [self._compile_node(arg) for arg in node.args]

        # 对于需要数值参数的运算符，提取字面量值
        # Polars 表达式不能直接作为窗口大小参数
        final_args = []
        for i, arg in enumerate(node.args):
            if isinstance(arg, NumberNode):
                final_args.append(arg.value)
            elif isinstance(arg, FeatureNode):
                final_args.append(self._compile_node(arg))
            elif isinstance(arg, CallNode):
                final_args.append(self._compile_node(arg))
            elif isinstance(arg, BinOpNode):
                final_args.append(self._compile_node(arg))
            else:
                final_args.append(self._compile_node(arg))

        return func(*final_args)

    @classmethod
    def compile_expr(cls, node: ASTNode) -> pl.Expr:
        """便捷方法：直接编译 AST 为 Polars 表达式"""
        return cls().compile(node)

    @classmethod
    def evaluate(cls, df: pl.DataFrame, expr_text: str, alias: str | None = None) -> pl.DataFrame:
        """便捷方法：解析 + 编译 + 执行

        Args:
            df: 输入 DataFrame
            expr_text: DSL 表达式字符串
            alias: 结果列名（默认使用表达式原文）

        Returns:
            添加了因子列的 DataFrame
        """
        from .parser import Parser

        ast = Parser.parse_expr(expr_text)
        expr = cls.compile_expr(ast)
        col_name = alias or expr_text
        return df.with_columns(expr.alias(col_name))
