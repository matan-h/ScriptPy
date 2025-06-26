import ast, io, tokenize, token
from collections.abc import Iterable


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
    def token_level_transform(editor):
        """
        Transform the token stream to replace the pattern 'left |.attr' with 'left | _apipe('attr',...)'.
        """
        while editor.has_more():
            current_token = editor.current
            assert current_token; # for typing

            # Check for the specific pattern: '| . NAME'
            # Ensure there are enough tokens to peek ahead (at least 3: |, ., NAME)
            dot_token = editor.peek(1)
            name_token = editor.peek(2)

            if (
                current_token.type == token.OP and current_token.string == "|" and
                dot_token and dot_token.type == token.OP and dot_token.string == "." and
                name_token and name_token.type == token.NAME
            ):

                # We've matched '| . NAME'. Extract relevant tokens.

                # Now, check for an optional argument list in parentheses: '( ... )'
                # Start peeking from the token after 'NAME', which is at offset 3 from '|'
                arg_start_offset = 3
                args_within_parens = []
                arg_start = editor.peek(arg_start_offset)

                # Check if an opening parenthesis exists immediately after 'NAME'
                if arg_start and arg_start.string == "(":
                    depth = 1 # Keep track of parenthesis nesting level
                    current_peek_offset = arg_start_offset + 1 # Move past the opening '('

                    # Collect tokens until the matching closing parenthesis is found
                    while editor.peek(current_peek_offset) and depth > 0:
                        peeked_token = editor.peek(current_peek_offset)
                        assert peeked_token; # for typing

                        if peeked_token.string == "(":
                            depth += 1
                        elif peeked_token.string == ")":
                            depth -= 1

                        # Only append tokens that are *inside* the main parenthesis block
                        # and not the final closing parenthesis itself
                        if depth > 0:
                            args_within_parens.append(peeked_token)

                        current_peek_offset += 1 # Move to the next token to check

                    # The total number of tokens consumed by this pattern, including '(', args, ')'
                    total_consumed_tokens = current_peek_offset
                else:
                    # No parentheses found, so only '| . NAME' is consumed.
                    total_consumed_tokens = arg_start_offset # Which is 3 tokens (|, ., NAME)

                # Now, emit the transformed tokens: | _apipe('name', [args])
                editor.append(type=token.OP, string="|")
                editor.append(type=token.NAME, string="_apipe")
                editor.append(type=token.OP, string="(")
                editor.append(type=token.STRING, string=repr(name_token.string)) # 'name' as a string literal

                if args_within_parens:
                    editor.append(type=token.OP, string=",")
                    # Append all collected argument tokens
                    editor.extend(*args_within_parens)

                editor.append(type=token.OP, string=")")

                # Skip the original tokens that were consumed and replaced
                editor.skip(total_consumed_tokens)

                # Continue to the next iteration of the loop to process the next set of tokens
                continue

            # If the special pattern was not matched, simply append the current token
            # to the output list and move to the next token in the input stream.
            editor.append_current()

        # After the loop, return the final list of transformed tokens
