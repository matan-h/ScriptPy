import argparse
import ast
import io
import linecache
import tokenize
from typing import Type

import astor

from .TokenEditor import TokenEditor

from .pipes import PipeTransformer
from .commands import ShellTransformer
from .baseTransformer import BaseTransformer
from .smart_eval import balance_fix, smart_parse, smart_run


transformers: list[Type[BaseTransformer]] = [PipeTransformer, ShellTransformer]


def custom_eval(src: str, globals_: dict | None = None):
    # ——— 1) token-level rewrite of “|.name…” → “| _apipe('name',…)”
    src = balance_fix(src)


    toks = list(tokenize.generate_tokens(io.StringIO(src).readline))


    editor = TokenEditor(toks)

    for transformer in transformers:
        transformer.token_level_transform(editor)
        editor.commit()

    editor.end() # make sure output is not empty
    rewritten = tokenize.untokenize(editor.as_token_list())

    filename = '<main>'
    # using here rewritten for accurate syntax errors
    linecache.cache[filename] = (len(rewritten.encode('utf-8')), None, rewritten.splitlines(keepends=True) , filename)


    # ——— 2) AST parse & transform
    tree = smart_parse(rewritten, filename=filename)

    # update linecache here to use the original src for better errors.
    linecache.cache[filename] = (len(src.encode('utf-8')), None, src.splitlines(keepends=True) , filename)

    for transformer in transformers:
        tree = transformer().visit(tree)

    ast.fix_missing_locations(tree)
    print(f"[DEBUG] Transformed code:```\n{astor.to_source(tree).strip()}\n```\n")
    # code = compile(tree, filename, 'eval')

    # ——— 3) eval with our small helpers in scope
    env = {}
    for transformer in transformers:
        env.update(transformer.environment)

    if globals_:
        env.update(globals_)
    return smart_run(tree, globals_dict=env, filename=filename)


def main():
    parser = argparse.ArgumentParser(
        description="Run scriptpy code from a file or the command line."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("filename", nargs="?", help="scriptpy filename to execute")
    group.add_argument(
        "-c", "--code", type=str, help="scriptpy code provided as a string"
    )

    args = parser.parse_args()

    if args.filename:
        with open(args.filename, "r") as f:
            code = f.read()
        print(custom_eval(code))
    elif args.code:
        print(custom_eval(args.code))


if __name__ == "__main__":
    main()
