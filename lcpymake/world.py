import json
from pathlib import Path
from typing import List, Callable
from functools import wraps
from typing import Set


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
            construct_graph(self)
            self.is_built = True
        return func(self, *args, **kwargs)
    return wrapped


class World:

    def __init__(self, srcdir: Path, sandbox: Path):
        self.nodes: List[Node] = []
        self.srcdir = srcdir
        self.sandbox = sandbox
        self.is_built = False
        sandbox.mkdir(parents=True, exist_ok=True)
        self._root_nodes: Set[Node] = set()
        self._source_nodes: Set[Node] = set()
        self._first_candidate_for_build = None

    def find_node(self):
        return None

    @property
    @requires_built
    def root_nodes(self):
        return self._root_nodes

    @property
    @requires_built
    def source_nodes(self):
        return self._source_nodes

    @property
    @requires_built
    def first_candidate_for_build(self):
        return self._first_candidate_for_build

    @requires_built
    def to_json(self):
        world_dict = {}
        for node in self.nodes:
            j = node.to_json()
            world_dict.update({j["id"]: j})
        world_dict["root_nodes"] = [node.__repr__() for node in self.root_nodes]
        world_dict["source_nodes"] = [node.__repr__() for node in self.source_nodes]
        world_dict_str = json.dumps(world_dict)
        j = json.loads(world_dict_str)
        return j

    @mark_unbuilt
    def add_source_node(self, artefact: str, scan: Callable[[str], List[str]]):
        new_node = Node(artefacts=[artefact], sources=[], rule=None, scan=scan)
        try:
            self.nodes.append(new_node)
            return new_node
        except Exception as exception:
            self.nodes.pop()
            raise exception

    @mark_unbuilt
    def add_built_node(self, sources: List[str], artefacts: List[str], rule):
        new_node = Node(artefacts=artefacts, sources=sources, rule=rule,
                        scan=None)
        self.nodes.append(new_node)
        return new_node

    def json_path(self) -> Path:
        return self.sandbox / 'lcpymake.json'

    def stamp(self):
        with open(str(self.json_path()), 'w') as fout:
            json.dump(self._to_json(), fout)

    @mark_unbuilt
    def touch(self):
        pass

    @mark_unbuilt
    def build_one_step(self):
        logger.info("build_one_step")
        build_one_step(self)


from lcpymake.implem.construct_graph import construct_graph  # noqa E402
from lcpymake.implem.build import build_one_step  # noqa E402
from lcpymake import logger  # noqa E402
from lcpymake.node import Node  # noqa E402
