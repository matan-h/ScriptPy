import ast
import importlib
import importlib.util
import sys
from ..baseTransformer import BaseTransformer
blacklist = [
    "this", # can be confusing
]

import ast
import importlib
import importlib.util
import sys

class AutoImportTransformer(BaseTransformer):
    """Detects qualified module usage and inserts missing imports."""

    def __init__(self):
        super().__init__()
        self.detected_modules = set()
        self.existing_imports = set()

    def visit_Import(self, node: ast.Import):
        """Track existing imports."""
        for alias in node.names:
            self.existing_imports.add(alias.name)
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):

        """Detect module.attr patterns."""
        if isinstance(node.value, ast.Name):
            module_name = node.value.id
            attr = node.attr
            spec = importlib.util.find_spec(module_name)
            if spec:
                was_loaded = module_name in sys.modules
                try:
                    mod = importlib.import_module(module_name)
                    if hasattr(mod, attr):
                        self.detected_modules.add(module_name)
                except Exception:
                    pass
                finally:
                    if not was_loaded and module_name in sys.modules:
                        del sys.modules[module_name]

        return self.generic_visit(node)

    def visit_Module(self, node: ast.Module):
        """Insert missing imports."""
        self.generic_visit(node)
        new_imports = [
            ast.Import(names=[ast.alias(name=mod, asname=None)])
            for mod in sorted(self.detected_modules)
            if mod not in self.existing_imports
        ]
        node.body = new_imports + node.body
        return node

def detect_and_add_imports(code: str) -> str:
    """Detects module usage and adds missing imports."""
    try:
        tree = ast.parse(code)
        detector = AutoImportTransformer()
        modified_tree = detector.visit(tree)
        return ast.unparse(modified_tree)
    except SyntaxError as e:
        print(f"Syntax error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return code
