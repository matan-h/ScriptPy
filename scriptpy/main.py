import ast, io, tokenize
from typing import Type
import astor
import linecache

from .TokenEditor import TokenEditor

from .pipes import PipeTransformer
from .commands import ShellTransformer
from .baseTransformer import BaseTransformer

transformers:list[Type[BaseTransformer]] = [PipeTransformer,ShellTransformer]


def custom_eval(src, globals_=None, locals_=None):
    # ——— 1) token-level rewrite of “|.name…” → “| _apipe('name',…)”
    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))
    editor = TokenEditor(toks)

    for transformer in transformers:
        transformer.token_level_transform(editor)
        editor.commit()

    editor.end() # make sure output is not empty
    rewritten = tokenize.untokenize(editor.as_token_list())

    filename = '<main>'

    lines = src.splitlines(keepends=True) # src is the original, not fully accurate.
    linecache.cache[filename] = (len(src.encode('utf-8')), None, lines, filename)


    # ——— 2) AST parse & transform
    tree = ast.parse(rewritten, mode='eval', filename=filename)

    for transformer in transformers:
        tree = transformer().visit(tree)

    ast.fix_missing_locations(tree)
    print(f"[DEBUG] Transformed code:```\n{astor.to_source(tree).strip()}\n```\n")
    code = compile(tree, filename, 'eval')

    # ——— 3) eval with our small helpers in scope
    env = {}
    for transformer in transformers:
        env.update(transformer.environment)

    if globals_: env.update(globals_)
    return eval(code, env, locals_ or {})

# ——— examples ——————————————————————————————————————————————————
def main():
     main_command()


def main_command():
        # main_pipe()
        a  = (custom_eval("$('echo hi')"))
        assert a == "hi"
        print(custom_eval("$('ls -1 | wc -l')"))


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

    print(custom_eval("range(3) | str |.zfill(2)"))     # ['00', '01', '02']

    print(custom_eval("[5+1j,5+2j,5+3j] |.imag"))

if __name__ == "__main__":
    main()