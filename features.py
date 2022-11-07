import ast
from dataclasses import dataclass, field
from typing import Union


@dataclass(frozen=False)
class Function:
    name: str
    lines: int
    max_depth: int = 0
    branches: int = 0
    calls: int = 0
    returns: int = 0
    raises: int = 0
    nested_funcs: list["Function"] = field(default_factory=list)


@dataclass()
class SourceFile:
    lines: int
    functions: list[Function] = field(default_factory=list)


def slice(node, f: Function, branch_depth: int = 0):
    if node is None:
        return
    if isinstance(node, ast.Index):
        stmt(node.value, f, branch_depth)
        return
    if isinstance(node, ast.Slice):
        stmt(node.lower, f, branch_depth)
        stmt(node.upper, f, branch_depth)
        stmt(node.step, f, branch_depth)
        return
    if isinstance(node, ast.ExtSlice):
        for dim in node.dims:
            slice(dim, f, branch_depth)
        return


def stmt(node, f: Function, branch_depth: int = 0):
    if node is None:
        return
    if branch_depth > f.max_depth:
        f.max_depth = branch_depth
    if isinstance(node, (ast.Name, ast.JoinedStr, ast.Constant, ast.Global)):
        # Skip
        return
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        for elt in node.elts:
            stmt(elt, f, branch_depth)
        return
    if isinstance(node, ast.Dict):
        for key in node.keys:
            stmt(key, f, branch_depth)
        for val in node.values:
            stmt(val, f, branch_depth)
        return
    if isinstance(node, ast.Expr):
        return stmt(node.value, f, branch_depth)
    if isinstance(node, ast.NamedExpr):
        return stmt(node.value, f, branch_depth)
    if isinstance(node, ast.UnaryOp):
        return stmt(node.operand, f, branch_depth)
    if isinstance(node, ast.BinOp):
        stmt(node.left, f, branch_depth)
        return stmt(node.right, f, branch_depth)
    if isinstance(node, ast.BoolOp):
        for value in node.values:
            stmt(value, f, branch_depth)
        return
    if isinstance(node, ast.Compare):
        stmt(node.left, f, branch_depth)
        for value in node.comparators:
            stmt(value, f, branch_depth)
        return
    if isinstance(node, ast.Call):
        f.calls += 1
        stmt(node.func, f, branch_depth)
        for arg in node.args:
            stmt(arg, f, branch_depth)
        for kw_arg in node.keywords:
            stmt(kw_arg.value, f, branch_depth)
        return
    if isinstance(node, ast.IfExp):
        f.branches += 1
        stmt(node.test, f, branch_depth)
        stmt(node.body, f, branch_depth + 1)
        stmt(node.orelse, f, branch_depth + 1)
        return
    if isinstance(node, ast.Attribute):
        stmt(node.value, f, branch_depth)
        return
    if isinstance(node, ast.Subscript):
        stmt(node.value, f, branch_depth)
        slice(node.slice, f, branch_depth)
        return
    if isinstance(node, ast.Assign):
        for target in node.targets:
            stmt(target, f, branch_depth)
        stmt(node.value, f, branch_depth)
        return
    if isinstance(node, ast.AugAssign):
        stmt(node.target, f, branch_depth)
        stmt(node.value, f, branch_depth)
        return
    if isinstance(node, ast.AnnAssign):
        stmt(node.target, f, branch_depth)
        stmt(node.value, f, branch_depth)
        return
    if isinstance(node, ast.If):
        stmt(node.test, f, branch_depth)
        f.branches += 1
        for child in node.body:
            stmt(child, f, branch_depth + 1)
        for child in node.orelse:
            if isinstance(child, ast.If):
                stmt(child, f, branch_depth)
            else:
                f.branches += 1
                stmt(child, f, branch_depth + 1)
        return
    if isinstance(node, (ast.For, ast.AsyncFor)):
        stmt(node.iter, f, branch_depth)
        f.branches += 1
        for child in node.body:
            stmt(child, f, branch_depth + 1)
        if node.orelse:
            f.branches += 1
            for child in node.orelse:
                stmt(child, f, branch_depth + 1)
        return
    if isinstance(node, ast.While):
        stmt(node.test, f, branch_depth + 1)
        f.branches += 1
        for child in node.body:
            stmt(child, f, branch_depth + 1)
        if node.orelse:
            f.branches += 1
            for child in node.orelse:
                stmt(child, f, branch_depth + 1)
        return
    # if isinstance(node, ast.Match):
    #     print("skipped match statement: not implemented")
    #     return
    if isinstance(node, ast.Await):
        return stmt(node.value, f, branch_depth)
    if isinstance(node, ast.Try):
        f.branches += 1
        for child in node.body:
            stmt(child, f, branch_depth + 1)
        for handler in node.handlers:
            f.branches += 1
            except_handler(handler, f, branch_depth + 1)
        if node.orelse:
            f.branches += 1
            for child in node.orelse:
                stmt(child, f, branch_depth + 1)
        for child in node.finalbody:
            stmt(child, f, branch_depth + 1)
        return
    if isinstance(node, (ast.With, ast.AsyncWith)):
        for item in node.items:
            stmt(item.context_expr, f, branch_depth)
        for child in node.body:
            stmt(child, f, branch_depth)
        return
    if isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)):
        f.returns += 1
        stmt(node.value, f, branch_depth)
        return
    if isinstance(node, ast.Raise):
        f.raises += 1
        stmt(node.exc, f, branch_depth)
        return
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        analyze_item(node, f.nested_funcs, branch_depth)
        return
    print(f"Skipped {type(node)}")


def except_handler(node: ast.ExceptHandler, f: Function, branch_depth: int):
    for child in node.body:
        stmt(child, f, branch_depth)


def function_def(node: Union[ast.FunctionDef, ast.AsyncFunctionDef], branch_depth: int = 0) -> Function:
    ret = Function(name=node.name, lines=node.end_lineno - node.lineno + 1)
    for child in node.body:
        stmt(child, ret, branch_depth)
    return ret


def class_def(node: ast.ClassDef, branch_depth: int = 0) -> list[Function]:
    funcs = []
    for item in node.body:
        analyze_item(item, funcs, branch_depth)
    return funcs


def analyze_file(file_path: str) -> SourceFile:
    with open(file_path, mode='r') as fp:
        source = fp.read()
        root: ast.Module = ast.parse(source, mode='exec')

    functions = []
    for item in root.body:
        analyze_item(item, functions)

    lines = len(source.split('\n'))
    return SourceFile(functions=functions, lines=lines)


def analyze_item(node, funcs: list[Function], branch_depth: int = 0):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        funcs.append(function_def(node, branch_depth))
    elif isinstance(node, ast.ClassDef):
        funcs.extend(class_def(node, branch_depth))
