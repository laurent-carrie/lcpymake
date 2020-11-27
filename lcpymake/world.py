import json
from pathlib import Path
from typing import List, Callable
from functools import wraps


from lcpymake.node import Node


def mark_unbuilt(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        self.is_built = False
        return func(self, *args, **kwargs)
    return wrapped


def requires_built(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if not self.is_built:
            build_graph(self)
            self.is_built = False
        return func(self, *args, **kwargs)
    return wrapped


class World:

    def __init__(self, srcdir: Path, sandbox: Path):
        self.nodes: List[Node] = []
        self.srcdir = srcdir
        self.sandbox = sandbox
        self.is_built = False
        sandbox.mkdir(parents=True, exist_ok=True)
        self._root_nodes = set()

    def find_node(self):
        return None

    @requires_built
    def root_nodes(self):
        return self._root_nodes

    def to_json(self):
        world_dict = [n.to_json() for n in self.nodes]
        world_dict_str = json.dumps(world_dict)
        j = json.loads(world_dict_str)
        return j

    @mark_unbuilt
    def add_source_node(self, artefact: str, scan: Callable[[str], List[str]]):
        new_node = Node(srcdir=self.srcdir, sandbox=self.sandbox,
                        artefacts=[('', artefact)], sources=[], rule=None, scan=scan, get_node=self.find_node)
        new_node.is_scanned = False
        new_node.is_source = True
        try:
            self.nodes.append(new_node)
            return new_node
        except Exception as exception:
            self.nodes.pop()
            raise exception

    @mark_unbuilt
    def add_built_node(self, sources: List[str], artefacts: List[str], rule):
        new_node = Node(srcdir=self.srcdir, sandbox=self.sandbox,
                        artefacts=[('', artefact) for artefact in artefacts], sources=[], rule=None,
                        scan=None,
                        get_node=self.find_node)
        new_node.is_scanned = False
        new_node.is_source = False
        try:
            self.nodes.append(new_node)
            return new_node
        except Exception as exception:
            self.nodes.pop()
            raise exception

    def _mount(self, allow_missing):
        pass

    def scan(self):
        pass

    def json_path(self) -> Path:
        return self.sandbox / 'lcpymake.json'

    def _stamp(self):
        with open(str(self.json_path()), 'w') as fout:
            json.dump(self._to_json(), fout)


from lcpymake.implem.build_graph import build_graph  # noqa E402
