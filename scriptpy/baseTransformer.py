from abc import ABC, abstractmethod
import ast
from tokenize import TokenInfo


class BaseTransformer(ABC,ast.NodeTransformer):
    """
    Base class for code transformations.
    """
    environment:dict = {}

    @staticmethod
    @abstractmethod
    def token_level_transform(toks:list[TokenInfo])->list[TokenInfo]:
        """
        Abstract method to transform the code at the token level. (before AST visiting)
        """
        return toks

    def visit(self, node):
        """
        Visit a node and apply the transformation.
        This method can be overridden if needed.
        """
        return super().visit(node)