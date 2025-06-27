import argparse
import ast
import io
import linecache
import tokenize
import sys

import astor

from .TokenEditor import TokenEditor

from .transformers import transformers
from .smart_eval import balance_fix, smart_parse, smart_run




def custom_eval(src: str, globals_: dict | None = None,verbose=False):
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
    if verbose:
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
    description="Run scriptpy code snippets or script files, with optional data input."
)
    # Positional snippet treated as code by default
    parser.add_argument(
        'snippet',
        nargs='?',
        help="scriptpy code snippet to execute (default) unless --script is used"
    )
    # Script file option
    parser.add_argument(
        '-s', '--script',
        dest='filename',
        help="Path to scriptpy script file to execute; use '-' for stdin"
    )
    # Data file option
    parser.add_argument(
        '-d', '--data',
        dest='data_file',
        help="Filename to read as 'data' variable; use '-' for stdin"
    )
    parser.add_argument(
        '-c',
        dest='csnippet',
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Determine code source: script file or positional snippet
    if args.filename:
        if args.filename == '-':
            code_to_run = sys.stdin.read()
        else:
            with open(args.filename, 'r') as f:
                code_to_run = f.read()
    elif args.snippet:
        code_to_run = args.snippet
    elif args.csnippet: # allow "-c" just because people use that in python
        code_to_run = args.csnippet
    else:
        parser.error('No code provided. Use positional snippet or -s/--script for files.')

    # Load data if requested
    globals_dict = {}
    if args.data_file:
        if args.data_file == '-':
            data_content = sys.stdin.read()
        else:
            with open(args.data_file, 'r') as df:
                data_content = df.read()
        globals_dict['data'] = data_content

    # Execute and print result
    result = custom_eval(code_to_run, globals_=globals_dict or None, verbose=args.verbose)
    print(result)



if __name__ == "__main__":
    main()
