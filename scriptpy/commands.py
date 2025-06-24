import tokenize,token
from .baseTransformer import BaseTransformer
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
            current_token = editor.current
            assert current_token; # for typing

            # Check for the pattern: '$ ( STRING )'
            # Need at least 4 tokens for this pattern: $, (, STRING, )
            open_paren_token = editor.peek(1)
            command_string_token = editor.peek(2)
            close_paren_token = editor.peek(3)

            if (
                current_token.type == token.OP and current_token.string == "$" and
                open_paren_token and open_paren_token.type == token.OP and open_paren_token.string == "(" and
                command_string_token and command_string_token.type == token.STRING  and
                close_paren_token and close_paren_token.type == token.OP and close_paren_token.string == ")"
            ):
                command_value = command_string_token.string

                # Heuristic to detect multi-variable assignment:
                # Look at the history (already processed tokens in the output list).
                # We are looking for a pattern like 'NAME, NAME, ... = ' right before the '$'
                is_multi_assignment = False
                # Check a reasonable window of previous tokens (e.g., 20 tokens)
                history_window = editor.get_output_history(20)

                found_eq = False
                found_comma_before_eq = False

                # Iterate backward through the history window
                for i in range(len(history_window) - 1, -1, -1):
                    t = history_window[i]
                    if t.type == token.OP and t.string == "=":
                        found_eq = True
                        # If '=' is found, now check for a comma *before* it in this window
                        # This ensures it's part of a multi-assignment, not just a single assignment.
                        for j in range(i - 1, -1, -1):
                            if history_window[j].type == token.OP and history_window[j].string == ",":
                                found_comma_before_eq = True
                                break # Found comma, so likely multi-assignment
                        break # Found '=', stop searching further back for '='

                    # Stop looking back if we encounter a newline, which typically
                    # marks the start of a new statement.
                    if t.type == token.NEWLINE:
                        break

                if found_eq and found_comma_before_eq:
                    is_multi_assignment = True

                # Emit the transformed tokens
                editor.append(type=token.NAME, string="_shell_exec_multi" if is_multi_assignment else "_shell_exec")
                editor.append(type=token.OP, string="(")
                editor.append(type=token.STRING, string=command_value) # The original string, e.g., '"curl -s ..."'
                editor.append(type=token.OP, string=")")

                # Skip the original tokens: $, (, STRING, ) (4 tokens)
                editor.skip(4)
                continue # Continue to the next token in the input stream

            # If no special pattern was matched, simply append the current token
            editor.append_current()


