import ast, io, tokenize, token
from collections.abc import Iterable
import astor
import linecache

from .baseTransformer import BaseTransformer

# ——— helpers ——————————————————————————————————————————————————


class PipeableList(list):
    def __or__(self, fn):
        if callable(fn):
            return PipeableList(map(fn, self))
        raise TypeError("Right-hand side must be callable")


def left_pipe(obj):
    if isinstance(obj, Iterable) and not isinstance(obj, (str, PipeableList)):
        return PipeableList(obj)
    return obj


def _attr_pipe(name, *args):
    """Return a function x→ x.name(*args)."""

    def attr_pipe(x):
        attr = getattr(x, name)
        if callable(attr):
            return attr(*args)
        return attr

    return attr_pipe


# ——— AST transform for plain “| func” and “|.method” ——————————————————


class PipeTransformer(BaseTransformer):
    environment =  {
            "_lpipe": left_pipe,
            "_apipe": _attr_pipe,
        }

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if not isinstance(node.op, ast.BitOr):
            return node

        # plain func-pipe:   expr | fn   →   _lpipe(expr) | (fn)
        return ast.BinOp(
            left=ast.Call(
                func=ast.Name(id="_lpipe", ctx=ast.Load()),
                args=[node.left],
                keywords=[],
            ),
            op=ast.BitOr(),
            right=node.right,
        )

    @staticmethod
    def token_level_transform(toks):
        out = []
        i = 0
        while i < len(toks):
            t = toks[i]
            if t.type == token.OP and t.string == "|" and i + 2 < len(toks):
                dot, name = toks[i + 1], toks[i + 2]
                if (
                    dot.type == token.OP
                    and dot.string == "."
                    and name.type == token.NAME
                ):
                    # collect optional args inside parentheses
                    j, args = i + 3, []
                    if j < len(toks) and toks[j].string == "(":
                        depth = 1
                        j += 1
                        while j < len(toks) and depth:
                            tt = toks[j]
                            if tt.string == "(":
                                depth += 1
                            elif tt.string == ")":
                                depth -= 1
                            if depth and tt.type != token.ENDMARKER:
                                args.append((tt.type, tt.string))
                            j += 1
                    # emit:   | _apipe('name' [ , args ] )
                    out.append((token.OP, "|"))
                    out.append((token.NAME, "_apipe"))
                    out.append((token.OP, "("))
                    out.append((token.STRING, repr(name.string)))
                    if args:
                        out.append((token.OP, ","))
                        out.extend(args)
                    out.append((token.OP, ")"))
                    i = j
                    continue
            out.append((t.type, t.string))
            i += 1
        return out
