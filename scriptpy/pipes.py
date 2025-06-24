import ast, io, tokenize, token
from collections.abc import Iterable
import astor
import linecache
# ——— helpers ——————————————————————————————————————————————————

class MyList(list):
    def __or__(self, fn):
        if callable(fn):
            return MyList(map(fn, self))
        raise TypeError("Right-hand side must be callable")

def left_pipe(obj):
    # wrap any non-str iterable into MyList so that “| func” works
    if isinstance(obj, Iterable) and not isinstance(obj, (str, MyList)):
        return MyList(obj)
    return obj

def _attr_pipe(name, *args):
    """Return a function x→ x.name(*args)."""
    def attr_pipe(x):
        return getattr(x, name)(*args)
    return attr_pipe

# ——— AST transform for plain “| func” and “|.method” ——————————————————

class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if not isinstance(node.op, ast.BitOr):
            return node


        # 2) plain func-pipe:   expr | fn   →   _lpipe(expr) | (fn)
        return ast.BinOp(
            left=ast.Call(
                func=ast.Name(id='_lpipe', ctx=ast.Load()),
                args=[node.left],
                keywords=[]
            ),
            op=ast.BitOr(),
            right=node.right
        )

def custom_eval(src, globals_=globals(), locals_=None):
    # ——— 1) token-level rewrite of “|.name…” → “| _apipe('name',…)”
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    out = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.type == token.OP and t.string == '|' and i+2 < len(toks):
            dot, name = toks[i+1], toks[i+2]
            if dot.type == token.OP and dot.string == '.' and name.type == token.NAME:
                # collect optional args inside parentheses
                j, args = i+3, []
                if j < len(toks) and toks[j].string == '(':
                    depth = 1
                    j += 1
                    while j < len(toks) and depth:
                        tt = toks[j]
                        if tt.string == '(': depth += 1
                        elif tt.string == ')': depth -= 1
                        if depth and tt.type != token.ENDMARKER:
                            args.append((tt.type, tt.string))
                        j += 1
                # emit:   | _apipe('name' [ , args ] )
                out.append((token.OP, '|'))
                out.append((token.NAME, '_apipe'))
                out.append((token.OP, '('))
                out.append((token.STRING, repr(name.string)))
                if args:
                    out.append((token.OP, ','))
                    out.extend(args)
                out.append((token.OP, ')'))
                i = j
                continue
        out.append((t.type, t.string))
        i += 1

    rewritten = tokenize.untokenize(out)

    filename = '<pipe>'
    # linecache.cache[filename] = (size, mtime, lines, fullname)
    lines = src.splitlines(keepends=True) # src is the original, not fully accurate.
    # linecache.cache[filename] = (len(rewritten), None, lines, filename)
    linecache.cache[filename] = (len(rewritten.encode('utf-8')), None, lines, filename)


    # ——— 2) AST parse & transform
    tree = ast.parse(rewritten, mode='eval')
    tree = PipeTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    print(f"[DEBUG] Transformed code:```\n{astor.to_source(tree).strip()}\n```\n")
    code = compile(tree, '<pipe>', 'eval')

    # ——— 3) eval with our small helpers in scope
    env = {
        '_lpipe': left_pipe,
        '_apipe': _attr_pipe,
        'MyList': MyList
    }
    if globals_: env.update(globals_)
    return eval(code, env, locals_ or {})

# ——— examples ——————————————————————————————————————————————————

text = " aBc  cDe "

print(custom_eval("text.split() | str.upper"))
# ['ABC', 'CDE']

print(custom_eval("text.split() |.upper"))
# ['ABC', 'CDE']

print(custom_eval("[' foo', 'bar '] |.strip"))
# ['foo', 'bar']

print(custom_eval("['abc','bcd','cde'] |.replace('c','a') |.replace('c','d')"))
# ['aba', 'bad', 'ade']

print(custom_eval("range(3) | str |.zfill(2)"))

print(custom_eval("range(3) | str"))

# ['00', '01', '02']
# print(custom_eval("nameerror | nameerror"))

print(custom_eval("range(3)|str|.m"))

