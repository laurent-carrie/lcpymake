import hashlib
from enum import Enum, auto
from pathlib import Path
from typing import List, Tuple, Callable, Set, Optional
from lcpymake import logger


class Node:
    def __init__(self, srcdir: Path, sandbox: Path, artefacts: List[str], sources, rule,
                 scan: Optional["Rule"], get_node):
        self.srcdir = srcdir
        self.sandbox = sandbox
        self.artefacts = artefacts
        self.sources = sources
        self.in_nodes: Set[Node] = set()
        self.out_nodes: Set[Node] = set()
        self.scan = scan
        self.rule = rule
        self.get_node = get_node
        self.artefact_digest: Optional[str] = None
        self.stored_digest = None
        self.current_digest = None

    @property
    def is_source(self) -> bool:
        return self.sources == []

    @property
    def label(self) -> str:
        return ";".join(self.artefacts)

    def to_json(self):
        j = {}
        return j

    def __repr__(self):
        return ";".join(self.artefacts)


class Rule:
    def __init__(self, info: Callable[[List[str], List[str]], str],
                 run: Callable[[List[str], List[str]], bool]):
        self.info = info
        self.run = run
