from abc import ABC, abstractmethod
import ast
from .TokenEditor import TokenEditor


class BaseTransformer(ABC,ast.NodeTransformer):
    """
    Base class for code transformations.
    """
    environment:dict = {}

    @staticmethod
    @abstractmethod
    def token_level_transform(editor:TokenEditor)->None:
        """
        Abstract method to transform the code at the token level. (before AST visiting)
        """
        return

    def visit(self, node):
        """
        Visit a node and apply the transformation.
        This method can be overridden if needed.
        """
        return super().visit(node)