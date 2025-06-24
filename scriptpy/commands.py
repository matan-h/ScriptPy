import tokenize,token
from .baseTransformer import BaseTransformer
import ast
import subprocess
from io import StringIO

class ShellTransformer(BaseTransformer):
    """
    A transformer that run shell commands on $(command) syntax.
    """
    environment = {
        "$": lambda cmd: StringIO(
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True).stdout
        )
    }

    @staticmethod
    def token_level_transform(toks):
        out = []
        i = 0
        while i < len(toks):
            tok = toks[i]
            print(tok,toks,type(tok))
            # tok_type, tok_str = toks[i]

            # Look for $ followed by (
            if tok.type == token.OP and tok.string == "$":
                if i + 1 < len(toks) and toks[i + 1][1] == "(":
                    # Replace `$` with NAME token for `shell`

                    out.append((token.NAME, "shell"))
                    i += 1  # skip the '$' token
                    continue  # let the '(' be processed normally

            # otherwise just copy the token
            out.append(tok)
            i += 1

        return out
    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == "$":
            if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                raise SyntaxError("Expected string literal in $('...') shell command")

            return ast.Call(
                func=ast.Name(id="$", ctx=ast.Load()),
                args=node.args,
                keywords=[]
            )
        return node
