from typing import Type

from scriptpy.baseTransformer import BaseTransformer
from .command import ShellTransformer
from .pipes import PipeTransformer
from .autoimport import AutoImportTransformer

transformers:list[Type[BaseTransformer]] = [
    ShellTransformer,
    PipeTransformer,


]

