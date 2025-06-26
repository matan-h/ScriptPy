import tokenize,token
from ..baseTransformer import BaseTransformer
import ast
import subprocess
from io import StringIO

def shell_exec_base(cmd,check=True):
    return subprocess.run(cmd, shell=True, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def shell_exec(cmd):
    return shell_exec_base(cmd,check=True).stdout.strip()

def shell_exec_multi(cmd):
    res = shell_exec_base(cmd,check=False)
    return res.stdout.strip(), res.stderr.strip(), res.returncode


class ShellTransformer(BaseTransformer):
    """
    A transformer that run shell commands on $(command) syntax. inspired by zx.

    It supports both single variable assignments and magical multi-variable assignments.
    it can handle:

    ```python
    response = $(curl -s https://example.com | jq '.data[] | .name')
    # and
    stdout,stderr,return_code = $(curl -s https://example.com | jq '.data[] | .name')
    ```
    """
    environment = {
        "_shell_exec": shell_exec,
        "_shell_exec_multi": shell_exec_multi,
    }
    @staticmethod
    def token_level_transform(editor):
        while editor.has_more():
            current = editor.current
            assert current  # for typing

            # Look for the $(
            if current.type == token.OP and current.string == "$":
                lp = editor.peek(1)
                if lp and lp.type == token.OP and lp.string == "(":
                    # Heuristic for multi-assignment:
                    history = editor.get_output_history(20)
                    found_eq = any(t.type == token.OP and t.string == "=" for t in history)
                    found_comma = False
                    if found_eq:
                        for t in reversed(history):
                            if t.type == token.NEWLINE:
                                break
                            if t.type == token.OP and t.string == ",":
                                found_comma = True
                                break
                    is_multi = found_eq and found_comma

                    # Skip the "$" and "("
                    editor.skip(2)

                    # Collect everything up to the matching ")"
                    depth = 1
                    collected = []
                    while editor.has_more():
                        t = editor.current
                        assert t  # for typing

                        if t.type == token.OP:
                            if t.string == "(":
                                depth += 1
                            elif t.string == ")":
                                depth -= 1
                                # consume the closing ")"
                                editor.skip(1)
                                break
                        collected.append(t)
                        editor.skip(1)

                    # Emit the shell-exec call
                    editor.append(type=token.NAME,
                                  string="_shell_exec_multi" if is_multi else "_shell_exec")
                    editor.append(type=token.OP, string="(")
                    # replay the collected tokens inside the call
                    for tok in collected:
                        editor.append(type=tok.type, string=tok.string)
                    editor.append(type=token.OP, string=")")

                    continue

            # Fallback: copy token through unchanged
            editor.append_current()




