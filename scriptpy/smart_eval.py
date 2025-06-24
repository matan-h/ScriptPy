import ast
import io
import tokenize
from contextlib import _RedirectStream


class redirect_stdin(
    _RedirectStream
):  # https://github.com/pyodide/pyodide/blob/main/docs/usage/faq.md
    _stream = "stdin"



def balance_fix(s):
    stack = []
    try:
        tokens = tokenize.tokenize(io.BytesIO(s.encode("utf-8")).readline)
        for tok in tokens:
            tok_type = tok.type
            tok_str = tok.string
            if not tok_str:
                continue

            if tok_type in (tokenize.STRING, tokenize.COMMENT):
                continue  # Ignore brackets inside strings/comments
            if tok_str in "([{":
                stack.append({"(": ")", "[": "]", "{": "}"}[tok_str])
            elif tok_str in ")]}":
                if stack and stack[-1] == tok_str:
                    stack.pop()
                # Else: ignore mismatched closing brackets
    except (tokenize.TokenError, IndentationError):
        pass  # Handle unterminated tokens or other errors
    return s + "".join(reversed(stack))

def smart_parse(code, filename):
    """
    Parse the given code into an AST, handling SyntaxError by attempting to fix
    unbalanced parentheses, brackets, or braces.
    """
    try:
        return ast.parse(code, mode="exec", filename=filename)
    except SyntaxError:
        try:
            fixed_code = balance_fix(code)
            return ast.parse(fixed_code, mode="exec", filename=filename)
        except SyntaxError as e:
            raise


def smart_run(
    tree:ast.Module, globals_dict=None
):  # inspired by pyodide CodeRunner : https://github.com/pyodide/pyodide/blob/4fbbbedc09496c6968086d69aadba75398718b13/src/py/_pyodide/_base.py#L172
    if globals_dict is None:
        globals_dict = {}


    last_stmt = tree.body[-1]

    if isinstance(last_stmt, ast.Expr):
        if len(tree.body) > 1:
            exec(
                compile(
                    ast.Module(body=tree.body[:-1], type_ignores=[]), "<ast>", "exec"
                ),
                globals_dict,
            )
        return eval(
            compile(ast.Expression(last_stmt.value), "<ast>", "eval"), globals_dict
        )
    else:
        exec(compile(tree, "<ast>", "exec"), globals_dict)
        return None




