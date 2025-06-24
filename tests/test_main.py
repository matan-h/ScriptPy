import pytest

# Import the function under test. Adjust the import path to match your package structure.
from scriptpy import custom_eval


def test_pipe_with_named_function():
    # Apply built-in abs to each list element
    assert custom_eval("[-1, 2, -3] | abs") == [1, 2, 3]


def test_pipe_attribute_access():
    # Access .upper on each string
    result = custom_eval("['hello', 'world'] |.upper")
    assert result == ['HELLO', 'WORLD']


def test_pipe_method_call_with_args():
    # Replace characters in each string
    src = "['apple', 'banana', 'cherry'] |.replace('a','A')"
    result = custom_eval(src)
    assert result == ['Apple', 'bAnAnA', 'cherry']


def test_pipe_chaining():
    # Chain multiple transformations
    src = "['abc', 'bcd', 'cde'] |.replace('c','x') |.replace('x','z')"
    assert custom_eval(src) == ['abz', 'bzd', 'zde']


def test_shell_simple_echo():
    # Simple echo should strip trailing newline
    output = custom_eval("$('echo hi')")
    assert output == 'hi'


def test_shell_stdout_stderr_returncode():
    # Generate distinct stdout, stderr, and exit code
    cmd = (
        "a,b,c = $(\"python -c 'import sys; sys.stdout.write(\\\"OUT\\\");"
        " sys.stderr.write(\\\"ERR\\\"); sys.exit(5)'\")\n(a,b,c)"
    )
    res = custom_eval(cmd)
    assert res;

    stdout, stderr, code = res # type: ignore
    assert stdout == 'OUT'
    assert stderr == 'ERR'
    assert code == 5


def test_pipe_on_generator():
    # Test that generators (e.g., range) also work
    result = custom_eval("range(4) | str |.zfill(2)")
    assert result == ['00', '01', '02', '03']
