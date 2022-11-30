import ast
from dataclasses import dataclass, field
from typing import Optional, Union


@dataclass(frozen=False)
class Function:
    """Statistics and identifying information for a single function.

    Since the `dataclasses` library was used to create this class, documentation cannot be generated
    for it. See the source code for a more accurate representation of the program structure.
    """
    # The name of the function
    name: str
    # The line that the function starts on
    start_line: int
    # The number of lines of code that the function takes up
    lines: int
    # The class that this function is defined inside of, if any
    enclosing_class: Optional[str]
    # The maximum branch depth reached in the function body
    max_depth: int = 0
    # The number of branch points in the function body
    branches: int = 0
    # The number of function calls in the function body
    calls: int = 0
    # The number of `return` statements in the function body
    returns: int = 0
    # The number of `raises` statements in the function body
    raises: int = 0
    # The number of `assert` statements in the function body
    assertions: int = 0
    # Any functions that are defined in the function body
    nested_funcs: list["Function"] = field(default_factory=list)


@dataclass()
class SourceFile:
    """A wrapper around a single source file.

    Since the `dataclasses` library was used to create this class, documentation cannot be generated
    for it. See the source code for a more accurate representation of the program structure.
    """
    # The number of lines in the file
    lines: int
    # Any function that are defined in the file
    functions: list[Function] = field(default_factory=list)


def slice_(node, f: Function, branch_depth: int = 0):
    """Handles slice syntax as that can get rather complicated.
    For example, numpy arrays allow multidimensional slicing like
    `A[:,1:5, :10]`

    :param node: The AST root node to traverse
    :param f: The most recent enclosing function, if any
    :param branch_depth: The current recursive branch depth. Defaults to 0
    """
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
            slice_(dim, f, branch_depth)
        return


# AST elements we don't care about. Roughly, these are the leaf nodes of
# the abstract syntax tree.
_SKIP_THESE = (
    ast.Name,
    ast.JoinedStr,
    ast.Constant,
    ast.Global,
    ast.Pass,
    ast.Import,
    ast.ImportFrom,
    ast.Delete,
    ast.Continue,
    ast.Break,
    ast.Lambda,
)


def stmt(node, f: Function, branch_depth: int = 0):
    """Recursively traverses a single statement and collects code statistics.

    This could probably be made far more efficient, but it works well for our purposes.

    :param node: The AST node to traverse
    :param f: The most recent enclosing function
    :param branch_depth: The current recursive branch depth. Defaults to 0.
    """
    if node is None:
        # It's not clear that this can ever happen
        return
    if branch_depth > f.max_depth:
        f.max_depth = branch_depth
    if isinstance(node, _SKIP_THESE):
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
    if isinstance(node, ast.Assert):
        f.assertions += 1
        return stmt(node.test, f, branch_depth)
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
    if isinstance(node, ast.Starred):
        return stmt(node.value, f, branch_depth)
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
        stmt(node.elt, f, branch_depth)
        for gen in node.generators:
            comprehension(gen, f, branch_depth)
        return
    if isinstance(node, ast.DictComp):
        stmt(node.key, f, branch_depth)
        stmt(node.value, f, branch_depth)
        for gen in node.generators:
            comprehension(gen, f, branch_depth)
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
        slice_(node.slice, f, branch_depth)
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
    # Our code runs on Python version 3.9, which doesn't yet have match statements.
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
        analyze_item(node, f.nested_funcs, None, branch_depth)
        return
    print(f"Skipped {type(node)}")


def comprehension(node: ast.comprehension, f: Function, branch_depth: int = 0):
    """Handles list, tuple, and dictionary comprehensions

    :param node: The AST node to traverse
    :param f: The most recent enclosing function
    :param branch_depth: The current recursive branch depth. Defaults to 0.
    """
    f.branches += len(node.ifs)
    stmt(node.iter, f, branch_depth)


def except_handler(node: ast.ExceptHandler, f: Function, branch_depth: int):
    """Handles `except` blocks

    :param node: The AST node to traverse
    :param f: The most recent enclosing function
    :param branch_depth: The current recursive branch depth. Defaults to 0.
    """
    for child in node.body:
        stmt(child, f, branch_depth)


def function_def(node: Union[ast.FunctionDef, ast.AsyncFunctionDef], enclosing_class: Optional[str], branch_depth: int = 0) -> Function:
    """Traverses a function definition and returns a statistical representation of the function body.

    :param node: The AST node to traverse
    :param enclosing_class: The most recent enclosing class, if any
    :param branch_depth: The current recursive branch depth. Defaults to 0.
    :return: A representation of the function, including all relevant statistics.
    """
    ret = Function(
        name=node.name,
        start_line=node.lineno,
        lines=node.end_lineno - node.lineno + 1,
        enclosing_class=enclosing_class,
    )
    for child in node.body:
        stmt(child, ret, branch_depth)
    return ret


def class_def(node: ast.ClassDef, branch_depth: int = 0) -> list[Function]:
    """Traverses a class definition and returns a statistical representation of any functions defined inside.

    :param node: The AST node to traverse
    :param branch_depth: The current recursive branch depth. Defaults to 0.
    :return: A list of the functions that were defined inside the class.
    """
    funcs = []
    for item in node.body:
        analyze_item(item, funcs, node.name, branch_depth)
    return funcs


def analyze_file(file_path: str) -> SourceFile:
    """Analyze the file at the given path and return a statistical representation of its contents.

    :param file_path: The relative or absolute path to the file to analyze.
    :return: An in-memory representation of the contents of the file.
    """
    with open(file_path, mode='r') as fp:
        source = fp.read()
        root: ast.Module = ast.parse(source, mode='exec')

    functions = []
    for item in root.body:
        analyze_item(item, functions)

    lines = len(source.split('\n'))
    return SourceFile(functions=functions, lines=lines)


def analyze_item(node, funcs: list[Function], enclosing_class: Optional[str] = None, branch_depth: int = 0):
    """Analyzes a single item and adds any functions encountered to the list

    :param node: The AST node to traverse.
    :param funcs: The list of functions that any new functions will be added to.
    :param enclosing_class: The most recent enclosing class, if any.
    :param branch_depth: The current recursive branch depth. Defaults to 0.
    """
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        funcs.append(function_def(node, enclosing_class, branch_depth))
    elif isinstance(node, ast.ClassDef):
        funcs.extend(class_def(node, branch_depth))
