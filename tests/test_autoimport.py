import pytest
from textwrap import dedent
import ast

from scriptpy.transformers.autoimport import detect_and_add_imports


import pytest
from textwrap import dedent
import ast
import pytest
from textwrap import dedent


def extract_imports(code: str) -> list[str]:
    """Return list of import statements as strings from code."""
    tree = ast.parse(code)
    imports = []
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(f"import {alias.name}")
        else:
            break  # Stop at first non-import statement (assumes all imports are at top)
    return sorted(imports)


@pytest.mark.parametrize(
    "input_code, expected_imports",
    [
        (
            "print(os.path.join('a', 'b'))\nmy_args = sys.argv[1:]\n",
            ["import os", "import sys"],
        ),
        (
            """
            value = math.pi
            data = json.loads('{}')
            non_existent_func = non_existent_mod.some_func()
            """,
            ["import json", "import math"],
        ),
        (
            """
            import datetime
            today = datetime.date.today()
            my_variable = 10
            """,
            ["import datetime"],
        ),
        (
            "result = definitely_not_a_real_module.some_function_that_does_not_exist()\n",
            [],
        ),
        (
            """
            from functools import reduce
            from collections import defaultdict

            print(json.dumps({'key': 'value'}))
            my_dict = defaultdict(list)
            current_platform = sys.platform
            result = hashlib.non_existent_hash_func('test')
            """,
            [
                "import json",
                "import sys",
            ],
        ),
    ]
)
def test_detect_and_add_imports_ast(input_code, expected_imports):
    input_code = dedent(input_code)
    modified_code = detect_and_add_imports(input_code)

    actual_imports = extract_imports(modified_code)

    assert sorted(actual_imports) == sorted(expected_imports), (
        f"Expected imports: {expected_imports}\n"
        f"Actual imports:   {actual_imports}\n"
    )
