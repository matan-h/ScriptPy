import token # Provides constants for token types (e.g., token.OP, token.NAME, token.STRING)
import dataclasses
from tokenize import TokenInfo
from typing import List, Tuple, Union, Callable
import astor
@dataclasses.dataclass
class SimpleToken:
    type: int
    string: str

class TokenEditor:
    """
    A utility class designed to simplify the process of manually editing and
    transforming a list of `TokenInfo` objects.

    It provides a stream-like interface to navigate through the input tokens,
    inspect them, and build a new, transformed list of tokens without
    requiring manual index management or explicit list appending.

    Usage:
    1. Initialize with a list of TokenInfo objects: `editor = TokenEditor(toks)`
    2. Loop using `while editor.has_more():`
    3. Use `editor.current`, `editor.peek()` to inspect tokens.
    4. Use `editor.append_current()`, `editor.append()`, or `editor.skip()`
       to control which tokens are added to the output and how the input
       pointer advances.
    5. Get the final result: `transformed_toks = editor.get_result()`
    """

    def __init__(self, toks: List[TokenInfo]):
        """
        Initializes the TokenEditor with a list of `TokenInfo` objects.

        A copy of the input tokens is made to ensure that the original list
        remains unchanged.

        Args:
            toks: The initial list of `TokenInfo` objects to be processed.
        """
        self._input_tokens = [SimpleToken(type=x.type,string=x.string) for x in toks]
        self._output_tokens = []         # This list will store the transformed tokens
        self._current_idx = 0            # The internal pointer to the current token in _input_tokens

    @property
    def current(self) -> Union[SimpleToken, None]:
        """
        Returns the `TokenInfo` object at the current position in the input list.

        Returns `None` if the editor's internal pointer has reached or
        exceeded the end of the input token list.
        """
        if self._current_idx < len(self._input_tokens):
            return self._input_tokens[self._current_idx]
        return None

    def peek(self, offset: int = 1) -> Union[SimpleToken, None]:
        """
        Returns a `TokenInfo` object located at an `offset` from the
        current position in the input list, without moving the internal pointer.

        This allows you to look ahead in the token stream to identify patterns.

        Args:
            offset: The number of tokens to look ahead (positive value).
                    A value of 1 (default) means looking at the very next token.

        Returns:
            The `TokenInfo` object at the calculated offset, or `None` if the
            offset falls outside the bounds of the input token list.
        """
        target_idx = self._current_idx + offset
        if 0 <= target_idx < len(self._input_tokens):
            return self._input_tokens[target_idx]
        return None

    def advance(self, steps: int = 1):
        """
        Moves the internal pointer forward by the specified number of `steps`.
        This method effectively "consumes" tokens from the input stream.
        It does not add the consumed tokens to the output list.

        Args:
            steps: The number of positions to advance the pointer. Defaults to 1.
        """
        self._current_idx += steps

    def append_current(self):
        """
        Adds the `current` token (the token at the internal pointer's current
        position) to the `_output_tokens` list and then advances the
        internal pointer by one step.

        This is a convenience method for when a token is passed through
        without any specific transformation.
        """
        if self.current:
            self._output_tokens.append(self.current)
            self.advance(1)

    def append(self,type: int,string:str):
        self.extend(SimpleToken(type=type, string=string))

    def extend(self, *new_tokens: SimpleToken):
        """
        Adds one or more `TokenInfo` objects directly to the `_output_tokens` list.
        This method is used when you want to insert new tokens or replace existing
        ones with a new sequence.

        Crucially, this method does not affect the internal pointer for the
        input token stream. You must use `skip()` or `advance()` if you
        also intend to "consume" tokens from the input stream after appending.

        """
        self._output_tokens.extend(new_tokens)

    def skip(self, steps: int = 1):
        """
        Advances the internal pointer by the specified number of `steps` without
        adding the skipped tokens to the `_output_tokens` list.

        This is useful when a sequence of input tokens is recognized and needs
        to be effectively "deleted" or replaced by new tokens added via `append()`.

        Args:
            steps: The number of input tokens to skip. Defaults to 1.
        """
        self.advance(steps)

    def has_more(self) -> bool:
        """
        Checks if there are more tokens remaining in the input list to be processed.

        Returns:
            `True` if the internal pointer has not yet reached the end of the
            input token list, `False` otherwise.
        """
        return self._current_idx < len(self._input_tokens)

    def get_result(self) -> List[SimpleToken]:
        """
        Finalizes the transformation and returns the complete list of
        transformed `TokenInfo` objects.

        Before returning, this method ensures that any remaining tokens
        in the input list (those not explicitly processed by a transformation
        rule) are appended to the output list.

        Returns:
            A `List` of `TokenInfo` objects representing the final,
            transformed token stream.
        """
        # Automatically append any remaining tokens from the input
        # that were not explicitly handled by the transformation logic.
        while self.has_more():
            self.append_current()
        return self._output_tokens

    def get_output_history(self, count: int) -> List[SimpleToken]:
        """
        Returns the last 'count' tokens that have been appended to the output list.
        Useful for looking at the context that has already been processed and emitted.

        Args:
            count: The maximum number of tokens to retrieve from the end of the
                   output history.

        Returns:
            A list of `TokenInfo` objects from the end of the output history.
        """
        return self._output_tokens[-count:] if count <= len(self._output_tokens) else list(self._output_tokens)

    def as_token_list(self) -> List[Tuple[int, str]]:
        """
        Converts the current output tokens into a list of tuples
        (token type, token string) for untokenize.

        """
        return [(t.type, t.string) for t in self._output_tokens]

    def commit(self):
        """
        Commits the currently built output tokens as the new input tokens for subsequent operations.
        """
        # First, ensure any unprocessed tokens from the current input are moved to output
        while self.has_more():
            self.append_current()

        # The output of this pass becomes the input for the next pass
        self._input_tokens = list(self._output_tokens)
        self._output_tokens = [] # Clear the output buffer for the next pass
        self._current_idx = 0 # Reset pointer to the beginning of the new input

    def end(self):
        """
        just change the input to the output, so the all methods like as_token_list() will return the output
        """
        if self._output_tokens:
            raise ValueError("end the editor only after commit()")

        self._output_tokens = list(self._input_tokens)

