import hashlib
from enum import Enum, auto
from pathlib import Path
from typing import List, Tuple, Callable
from lcpymake import logger


class Node:
    def __init__(self, srcdir, sandbox, artefacts, sources, rule, scan, get_node):
        self.srcdir = srcdir
        self.sandbox = sandbox
        self.artefacts = artefacts
        self.sources = sources
        self.in_nodes = set()
        self.out_nodes = set()
        self.scan = scan
        self.rule = rule
        self.get_node = get_node

    @property
    def not_qualified_artefacts(self):
        return [f for (_, f) in self.artefacts]

    def deps_hash_hex(self):
        if self.is_source:
            return self.deps_hash_hex_of_source_node()
        else:
            return self.deps_hash_hex_of_built_node()

    def run(self):
        sources = [self.sandbox / f for (_, f) in self.sources]
        artefacts = [self.sandbox / f for (_, f) in self.artefacts]
        try:
            success = self.rule.run(sources=sources, targets=artefacts)
            return success
        except Exception:
            raise ValueError("rule failed")

    def to_json(self):
        j = {}
        return j

    def __repr__(self):
        return ";".join([name for (_, name) in self.artefacts])


class Rule:
    def __init__(self, info: Callable[[List[str], List[str]], str],
                 run: Callable[[List[str], List[str]], bool]):
        self.info = info
        self.run = run
