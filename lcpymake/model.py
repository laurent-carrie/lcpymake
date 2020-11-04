import json
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Set, Callable
import collections
# pylint:disable=E0401
# don't know why pylint complains about termcolor
from termcolor import colored
# pylint:enable=E0401


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


class SourceFileMissing(Exception):
    def __init__(self, filename):
        Exception.__init__(self)
        self.filename = filename


class Rule:
    def __init__(self, info: Callable[[List[str], List[str]], str],
                 run: Callable[[List[str], List[str]], bool]):
        self.info = info
        self.run = run


class NodeStatus(Enum):
    SOURCE_PRESENT = 1
    SOURCE_MISSING = 2
    BUILT_PRESENT = 3
    BUILT_MISSING = 4


class Node:
    node_id: int
    artefacts: List[Tuple[str, Path]]
    sources: List[Tuple[str, 'Path']]
    rule: str

    def __init__(self, srcdir, sandbox, artefacts, sources, rule):
        self.srcdir = srcdir
        self.sandbox = sandbox
        self.artefacts = artefacts
        if sources is None:
            self.sources = []
        else:
            self.sources = sources
        if len(sources) == 0:
            self.rule = None
            self.rule_info = None
        else:
            if rule is None:
                raise ValueError('rule not defined')
            self.rule = rule
            not_qualified_sources = [s for (_, s) in self.sources]
            not_qualified_artefacts = [s for (_, s) in self.artefacts]
            self.rule_info = rule.info(
                sources=not_qualified_sources, targets=not_qualified_artefacts)

    def run(self):
        sources = [self.sandbox / f for (_, f) in self.sources]
        artefacts = [self.sandbox / f for (_, f) in self.artefacts]
        self.rule.run(sources=sources, targets=artefacts)
        print(f'RRRRRRRRRRRRRRRRRRRRRRRRun {self.label}')

    @property
    def label(self):
        not_qualified_artefacts = [s for (_, s) in self.artefacts]
        return ';'.join(not_qualified_artefacts)

    def is_source(self) -> bool:
        return len(self.sources) == 0

    def to_json(self):
        world = {'artefacts': [str(p) for (_, p) in self.artefacts]}
        world.update({'status': self.status.name})
        if not self.is_source():
            world.update({'sources': [str(p) for (_, p) in self.sources]})
            world.update({'rule': self.rule_info})
        return world

    @property
    def status(self):
        if self.is_source():
            if {(self.srcdir / s).exists() for (_, s) in self.artefacts} == {True}:
                return NodeStatus.SOURCE_PRESENT
            return NodeStatus.SOURCE_MISSING
        if {(self.sandbox / s).exists() for (_, s) in self.artefacts} == {True}:
            return NodeStatus.BUILT_PRESENT
        return NodeStatus.BUILT_MISSING


class World:

    def __init__(self, srcdir: Path, sandbox: Path):
        self.nodes: List[Node] = []
        self.srcdir = srcdir
        self.sandbox = sandbox

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
        world_dict = [n.to_json() for n in self.nodes]
        world_dict_str = json.dumps(world_dict)
        j = json.loads(world_dict_str)
        return j

    def _add_source_node(self, artefact: str):
        new_node = Node(srcdir=self.srcdir, sandbox=self.sandbox,
                        artefacts=[('', artefact)], sources=[], rule=None)
        try:
            self.nodes.append(new_node)
            self._is_valid()
        except Exception as exception:
            self.nodes.pop()
            raise exception

    def _add_built_node(self, sources: List[str], artefacts: List[str], rule):
        artefacts = [('', f) for f in artefacts]
        sources = [('', f) for f in sources]
        new_node = Node(srcdir=self.srcdir, sandbox=self.sandbox,
                        artefacts=artefacts, sources=sources, rule=rule)
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

        def look_for_missing_source():
            for node in self.nodes:
                for (_, source) in node.sources:
                    self._find_node(source)
        look_for_missing_source()

    def _all_artefacts(self) -> Set[str]:
        return {artefact for node in self.nodes for (_, artefact) in node.artefacts}

    def _consumed_artefacts(self) -> Set[str]:
        return {source for node in self.nodes for (_, source) in node.sources}

    def _leaf_artefacts(self) -> Set[str]:
        return self._all_artefacts() - self._consumed_artefacts()

    def _leaf_nodes(self) -> Set[Node]:
        return {self._find_node(artefact) for artefact in self._leaf_artefacts()}

    def _print(self):
        def print_tree(indent, node):
            status = node.status
            if status == NodeStatus.SOURCE_PRESENT:
                # text = colored(node, 'red', attrs=['reverse', 'blink'])
                line1 = colored(node.label, 'green', attrs=[]) + ' (source)'
            elif status == NodeStatus.SOURCE_MISSING:
                line1 = colored(node.label, 'red', attrs=['blink']) + ' (missing source)'
            elif status == NodeStatus.BUILT_PRESENT:
                line1 = colored(node.label, 'blue', attrs=[]) + ' (built present)'
            elif status == NodeStatus.BUILT_MISSING:
                line1 = colored(node.label, 'blue', attrs=[
                                'reverse']) + ' (built missing)'
            else:
                raise Exception('internal error')
            print(f"{'.'*indent}{line1}")
            for (_, source) in node.sources:
                source_node = self._find_node(source)
                print_tree(indent + 1, source_node)

        for node in self._leaf_nodes():
            print_tree(0, node)

    def _mount(self):
        for node in self.nodes:
            if not node.is_source():
                continue
            for (_, f) in node.artefacts:
                if node.status != NodeStatus.SOURCE_PRESENT:
                    raise SourceFileMissing(f)
                (self.sandbox / f).parent.mkdir(parents=True, exist_ok=True)
                (self.sandbox / f).write_bytes((self.srcdir / f).read_bytes())

    def _not_built(self):
        return [node for node in self.nodes if node.status == NodeStatus.BUILT_MISSING]

    def _node_can_be_built(self, node: Node):
        if node.status != NodeStatus.BUILT_MISSING:
            return False
        for (_, source) in node.sources:
            node_source = self._find_node(source)
            if node_source.status in {NodeStatus.BUILT_MISSING, NodeStatus.SOURCE_MISSING}:
                return False
            if node_source.status in {NodeStatus.BUILT_PRESENT, NodeStatus.SOURCE_PRESENT}:
                continue
            raise Exception('implementation error')
        return True

    def _can_be_built(self) -> List[Node]:
        return [node for node in self.nodes if self._node_can_be_built(node)]

    def _build(self):
        self._mount()
        while True:
            before = len(self._not_built())
            for node in self._can_be_built():
                node.run()
            after = len(self._not_built())
            if after == 0:
                return True
            if before == after:
                return False
