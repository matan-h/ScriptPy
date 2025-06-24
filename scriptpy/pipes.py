import ast, io, tokenize, token
from collections.abc import Iterable
import astor
# ——— helpers ——————————————————————————————————————————————————

class MyList(list):
    def __or__(self, fn):
        if callable(fn):
            return MyList(map(fn, self))
        raise TypeError("Right-hand side must be callable")

def _pipeable(obj):
    # wrap any non-str iterable into MyList so that “| func” works
    if isinstance(obj, Iterable) and not isinstance(obj, (str, MyList)):
        return MyList(obj)
    return obj

def PIPE_ATTR(name, *args):
    """Return a function x→ x.name(*args)."""
    def _f(x):
        return getattr(x, name)(*args)
    return _f

# ——— AST transform for plain “| func” and “|.method” ——————————————————

class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if not isinstance(node.op, ast.BitOr):
            return node

        # 1) attribute-pipe: right = PIPE_ATTR(...) ?
        if (isinstance(node.right, ast.Call)
        and isinstance(node.right.func, ast.Name)
        and node.right.func.id == 'PIPE_ATTR'):
            name = node.right.args[0].value                # type: ignore # the method name
            args = node.right.args[1:]                     # its arguments
            return ast.ListComp(
                elt=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id='x', ctx=ast.Load()),
                        attr=name,
                        ctx=ast.Load()
                    ),
                    args=args,
                    keywords=[]
                ),
                generators=[
                    ast.comprehension(
                        target=ast.Name(id='x', ctx=ast.Store()),
                        iter=node.left,
                        ifs=[],
                        is_async=0
                    )
                ]
            )

        # 2) plain func-pipe:   expr | fn   →   _pipeable(expr) | (fn)
        return ast.BinOp(
            left=ast.Call(
                func=ast.Name(id='_pipeable', ctx=ast.Load()),
                args=[node.left],
                keywords=[]
            ),
            op=ast.BitOr(),
            right=node.right
        )

def custom_eval(src, globals_=globals(), locals_=None):
    # ——— 1) token-level rewrite of “|.name…” → “| PIPE_ATTR('name',…)”
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
                # emit:   | PIPE_ATTR('name' [ , args ] )
                out.append((token.OP, '|'))
                out.append((token.NAME, 'PIPE_ATTR'))
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

    # ——— 2) AST parse & transform
    tree = ast.parse(rewritten, mode='eval')
    tree = PipeTransformer().visit(tree)
    ast.fix_missing_locations(tree)
    print(f"[DEBUG] Transformed code:```\n{astor.to_source(tree).strip()}\n```\n")
    code = compile(tree, '<pipe>', 'eval')

    # ——— 3) eval with our small helpers in scope
    env = {
        '_pipeable': _pipeable,
        'PIPE_ATTR': PIPE_ATTR,
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
