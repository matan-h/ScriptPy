import ast, io, tokenize
from typing import Type
import astor
import linecache

from .pipes import PipeTransformer
from .commands import ShellTransformer
from .baseTransformer import BaseTransformer

transformers:list[Type[BaseTransformer]] = [PipeTransformer,ShellTransformer]


def custom_eval(src, globals_=None, locals_=None):
    # ——— 1) token-level rewrite of “|.name…” → “| _apipe('name',…)”
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))

    for transformer in transformers:
        toks =  transformer.token_level_transform(toks)


    rewritten = tokenize.untokenize(toks)

    filename = '<main>'

    lines = src.splitlines(keepends=True) # src is the original, not fully accurate.
    linecache.cache[filename] = (len(src.encode('utf-8')), None, lines, filename)


    # ——— 2) AST parse & transform
    tree = ast.parse(rewritten, mode='eval')

    for transformer in transformers:
        tree = transformer().visit(tree)

    ast.fix_missing_locations(tree)
    print(f"[DEBUG] Transformed code:```\n{astor.to_source(tree).strip()}\n```\n")
    code = compile(tree, '<pipe>', 'eval')

    # ——— 3) eval with our small helpers in scope
    env = {}
    for transformer in transformers:
        env.update(transformer.environment)

    if globals_: env.update(globals_)
    return eval(code, env, locals_ or {})

# ——— examples ——————————————————————————————————————————————————
def main():
        print(custom_eval("a = $(ls -l) | str.split() |.upper"))


def main_pipe():    # Example usage:
    text = " aBc  cDe "

    print(custom_eval("text.split() | str.upper",{'text': text}))
    # ['ABC', 'CDE']

    print(custom_eval("text.split() |.upper",{'text': text}))
    # ['ABC', 'CDE']

    print(custom_eval("[' foo', 'bar '] |.strip"))
    # ['foo', 'bar']

    print(custom_eval("['abc','bcd','cde'] |.replace('c','a') |.replace('c','d')"))
    # ['aba', 'bad', 'ade']

    print(custom_eval("range(3) | str |.zfill(2)"))

    print(custom_eval("range(3) | str"))

    # ['00', '01', '02']
    # print(custom_eval("nameerror | nameerror"))

    # print(custom_eval("range(3)|str|"))

    print(custom_eval("[5+1j,5+2j,5+3j] |.imag"))

if __name__ == "__main__":
    main()