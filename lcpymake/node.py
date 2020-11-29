import hashlib
from enum import Enum, auto
from pathlib import Path
from typing import List, Tuple, Callable, Set, Optional
from lcpymake import logger


class Rule:
    def __init__(self, info: Callable[[List[str], List[str]], str],
                 run: Callable[[List[str], List[str]], bool]):
        self.info = info
        self.run = run


class Node:
    def __init__(self, artefacts: List[str], sources, rule: Rule,
                 scan):
        self.artefacts = artefacts
        self.sources = sources
        self.in_nodes: Set[Node] = set()
        self.out_nodes: Set[Node] = set()
        self.scan = scan
        self.rule = rule
        self.artefact_digest: Optional[str] = None
        self.stored_digest = None
        self.current_digest = None

    @property
    def is_source(self) -> bool:
        return self.sources == []

    @property
    def is_up_to_date(self) -> bool:
        return self.stored_digest == self.current_digest

    @property
    def label(self) -> str:
        return ";".join(self.artefacts)

    def to_json(self):
        j = {
            "id": self.__repr__(),
            "artefacts": [str(f) for f in self.artefacts],
            "in": [node.__repr__() for node in self.in_nodes],
            "out": [node.__repr__() for node in self.out_nodes],
            "artefact_digest": self.artefact_digest,
            "stored_digest": self.stored_digest,
            "current_digest": self.current_digest
        }
        return j

    def __repr__(self):
        return ";".join(self.artefacts)
