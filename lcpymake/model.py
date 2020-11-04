import json
from pathlib import Path
from typing import List, Tuple
import collections


class ArtefactSeenSeveralTimes(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class NoSuchNode(Exception):
    def __init__(self):
        Exception.__init__(self)


class CannotAddARuleForASourceNode(Exception):
    def __init__(self):
        Exception.__init__(self)


class NodeAlreadyHasARule(Exception):
    def __init__(self):
        Exception.__init__(self)


class Rule:
    def __init__(self, info: str, run):
        self.info = info
        self.run = run


class Node:
    node_id: int
    artefacts: List[Tuple[str, Path]]
    deps: List[Tuple[str, 'Node']]
    rule: str

    def __init__(self, node_id, artefacts, deps, rule):
        self.node_id = node_id
        self.artefacts = artefacts
        if deps is None:
            self.deps = []
        else:
            self.deps = deps
        self.rule = rule

    def is_source(self) -> bool:
        return len(self.deps) == 0

    def to_json(self):
        return {'id': self.node_id, 'artefacts': [str(p) for (_, p) in self.artefacts]}


class World:

    def __init__(self):
        self.nodes: List[Node] = []

    def _find_node(self, filename) -> Node:
        # pylint:disable=W0120
        for node in self.nodes:
            for (_, filename_2) in node.artefacts:
                if filename == filename_2:
                    return node
            else:
                continue
        else:
            raise NoSuchNode()
        # pylint:enable=W0120

    def _to_json(self):
        world_dict = {n.node_id: n.to_json() for n in self.nodes}
        world_dict_str = json.dumps(world_dict)
        j = json.loads(world_dict_str)
        return j

    def _add_source_node(self, artefact: str):
        new_node = Node(node_id=len(self.nodes), artefacts=[
                        ('', artefact)], deps=None, rule=None)
        try:
            self.nodes.append(new_node)
            self._is_valid()
        except Exception as exception:
            self.nodes.pop()
            raise exception

    def _add_built_node(self, sources: List[str], artefacts: List[str], rule: Rule):
        print(sources)
        print(rule)
        artefacts = [('', f) for f in artefacts]
        new_node = Node(node_id=len(self.nodes),
                        artefacts=artefacts, deps=None, rule=None)
        try:
            self.nodes.append(new_node)
            self._is_valid()
        except Exception as exception:
            self.nodes.pop()
            raise exception

    def _is_valid(self):
        def look_for_doublons_in_artefacts():
            artefacts = [a for node in self.nodes for (_, a) in node.artefacts]
            counter = collections.Counter(artefacts).most_common(1)
            if counter == []:
                return
            (what, count) = counter[0]
            if count > 1:
                raise ArtefactSeenSeveralTimes(f'{what}')
        look_for_doublons_in_artefacts()
