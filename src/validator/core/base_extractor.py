from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator
from validator.core.models import Link


class BaseLinkExtractor(ABC):
    def __init__(self, source_file: Path) -> None:
        self.source_file = source_file

    @abstractmethod
    def get_links_from_file(self, file_content: str) -> Iterator[Link]:
        pass