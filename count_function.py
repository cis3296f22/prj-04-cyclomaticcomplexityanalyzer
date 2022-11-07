import ast

def count_function(filepath):
    with open(filepath) as file:
        tree = ast.parse(file.read())
        function_number = sum(isinstance(exp, ast.FunctionDef) for exp in tree.body)

        return function_number

