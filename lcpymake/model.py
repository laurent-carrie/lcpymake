import json
from enum import Enum
from pathlib import Path
from typing import List, Tuple, Set, Callable
import collections
import hashlib

# pylint:disable=E0401
# don't know why pylint complains about termcolor
from termcolor import colored
# pylint:enable=E0401


class ArtefactSeenSeveralTimes(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class NoSuchNode(Exception):
    def __init__(self, filename):
        Exception.__init__(self, f'{filename}')


class CannotAddARuleForASourceNode(Exception):
    def __init__(self):
        Exception.__init__(self)


class NodeAlreadyHasARule(Exception):
    def __init__(self):
        Exception.__init__(self)


class SourceFileMissing(Exception):
    def __init__(self, filename):
        Exception.__init__(self, f'source file missing : {filename}')
        self.filename = filename


class TargetArtefactNotBuilt(Exception):
    def __init__(self, filename):
        Exception.__init__(self, f'artefact was not built for : {filename}')
        self.filename = filename


class RuleFailed(Exception):
    def __init__(self, filename, msg):
        Exception.__init__(self, f'build failed for  : {filename} ; message is : {msg}')
        self.filename = filename
        self.msg = msg


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
    NEEDS_REBUILT = 5
    SCANNED_PRESENT_DEP = 6
    SCANNED_MISSING_DEP = 7


class Node:
    node_id: int
    artefacts: List[Tuple[str, Path]]
    sources: List[Tuple[str, 'Path']]
    rule: str

    def __init__(self, srcdir, sandbox, artefacts, sources, rule, scan):
        self.srcdir = srcdir
        self.sandbox = sandbox
        self.artefacts = artefacts
        self.is_source = None
        self.is_scanned = None
        self.deps = []
        self.ok_build = None
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
            not_qualified_sources = [Path(s) for (_, s) in self.sources]
            not_qualified_artefacts = [Path(s) for (_, s) in self.artefacts]
            self.rule_info = rule.info(
                sources=not_qualified_sources, targets=not_qualified_artefacts)
        self.scan = scan

    def deps_hash_hex(self):
        if self.is_source or self.is_scanned:
            raise Exception('implementation error')
        node_hash = hashlib.sha256()
        node_hash.update(str.encode(self.rule_info))
        for (_, s) in self.artefacts:
            f: Path = self.sandbox / s
            if f.exists():
                node_hash.update(f.read_bytes())
            else:
                return None
        for (_, s) in self.sources:
            f: Path = self.sandbox / s
            if f.exists():
                node_hash.update(f.read_bytes())
            else:
                return None
        for s in self.deps:
            f: Path = self.sandbox / s
            if f.exists():
                node_hash.update(f.read_bytes())
            else:
                return None
        return node_hash.hexdigest()

    def run(self):
        sources = [self.sandbox / f for (_, f) in self.sources]
        artefacts = [self.sandbox / f for (_, f) in self.artefacts]
        try:
            success = self.rule.run(sources=sources, targets=artefacts)
            return success
        except Exception as e:
            raise RuleFailed(self.rule_info, e) from e

    @property
    def label(self):
        not_qualified_artefacts = [str(s) for (_, s) in self.artefacts]
        return ';'.join(not_qualified_artefacts)

    def to_json(self):
        world = {'artefacts': [str(p) for (_, p) in self.artefacts]}
        world.update({'status': self.status.name})
        if not self.is_source and not self.is_scanned:
            world.update({'sources': [str(p) for (_, p) in self.sources]})
            world.update({'rule': self.rule_info})
        if self.is_source:
            world.update({'scanned_deps': [str(p) for p in self.deps]})
        if not (self.is_source or self.is_scanned):
            world.update({'digest': self.deps_hash_hex()})
            world.update({'ok_build': self.ok_build})

        return world

    @property
    def status(self):

        if self.is_scanned:
            return NodeStatus.SCANNED_PRESENT_DEP

        if self.is_source:
            if {(self.srcdir / s).exists() for (_, s) in self.artefacts} == {True}:
                return NodeStatus.SOURCE_PRESENT
            return NodeStatus.SOURCE_MISSING

        if {(self.sandbox / s).exists() for (_, s) in self.artefacts} == {True}:
            if self.ok_build is not None and (self.ok_build == self.deps_hash_hex()):
                return NodeStatus.BUILT_PRESENT
            return NodeStatus.NEEDS_REBUILT
        return NodeStatus.BUILT_MISSING


class World:

    def __init__(self, srcdir: Path, sandbox: Path):
        self.nodes: List[Node] = []
        self.srcdir = srcdir
        self.sandbox = sandbox
        sandbox.mkdir(parents=True, exist_ok=True)
        self.automatic_rules = {}

    def _find_node(self, filename) -> Node:
        # pylint:disable=W0120
        for node in self.nodes:
            for (_, filename_2) in node.artefacts:
                if filename == filename_2:
                    return node
            else:
                continue
        else:
            raise NoSuchNode(filename)
        # pylint:enable=W0120

    def _to_json(self):
        self._scan()
        self._mount(allow_missing=True)
        world_dict = [n.to_json() for n in self.nodes]
        world_dict_str = json.dumps(world_dict)
        j = json.loads(world_dict_str)
        return j

    def _add_source_node(self, artefact: str, scan: Callable[[str], List[str]]):
        new_node = Node(srcdir=self.srcdir, sandbox=self.sandbox,
                        artefacts=[('', artefact)], sources=[], rule=None, scan=scan)
        new_node.is_scanned = False
        new_node.is_source = True
        try:
            self.nodes.append(new_node)
            self._is_valid()
            return new_node
        except Exception as exception:
            self.nodes.pop()
            raise exception

    def _add_built_node(self, sources: List[str], artefacts: List[str], rule):
        artefacts = [('', f) for f in artefacts]
        sources = [('', f) for f in sources]
        new_node = Node(srcdir=self.srcdir, sandbox=self.sandbox,
                        artefacts=artefacts, sources=sources, rule=rule, scan=None)
        new_node.is_scanned = False
        new_node.is_source = False
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

    def _scanned_artefacts(self) -> Set[str]:
        return {filename for node in self.nodes for (_, filename)
                in node.artefacts if node.is_scanned}

    def _leaf_artefacts(self) -> Set[str]:
        return self._all_artefacts() - self._consumed_artefacts() - self._scanned_artefacts()

    def _leaf_nodes(self) -> Set[Node]:
        return {self._find_node(artefact) for artefact in self._leaf_artefacts()}

    def _print(self):
        def print_tree(indent, node):
            status = node.status
            if status == NodeStatus.SOURCE_PRESENT:
                # text = colored(node, 'red', attrs=['reverse', 'blink'])
                line1 = colored(node.label, 'green', attrs=[]) + ' (source)'
            elif status == NodeStatus.SOURCE_MISSING:
                line1 = colored(node.label, 'red', attrs=[
                                'reverse']) + ' (missing source)'
            elif status == NodeStatus.BUILT_PRESENT:
                line1 = colored(node.label, 'blue', attrs=[]) + ' (built present)'
            elif status == NodeStatus.SCANNED_PRESENT_DEP:
                line1 = colored(node.label, 'cyan', attrs=[]) + ' (scanned present)'
            elif status == NodeStatus.BUILT_MISSING:
                line1 = colored(node.label, 'blue', attrs=[
                                'reverse']) + ' (built missing)'
            elif status == NodeStatus.NEEDS_REBUILT:
                line1 = colored(node.label, 'red', attrs=[]) + ' (built not up to date)'
            else:
                raise Exception('internal error')
            print(f"{'...'*indent}{line1}")
            if not node.is_source:
                print(f"{'...'*(indent+1)}rule : {node.rule_info}")
            else:
                for fdep in node.deps:
                    line = colored(fdep, 'yellow', attrs=[]) + ' (scanned)'
                    print(f"{'...' * (indent + 1)}{line}")

            for (_, source) in node.sources:
                source_node = self._find_node(source)
                print_tree(indent + 1, source_node)

        for node in self._leaf_nodes():
            print_tree(0, node)

    def _mount(self, allow_missing):
        for node in self.nodes:
            if not (node.is_source or node.is_scanned):
                continue
            for (_, f) in node.artefacts:
                if node.status in {NodeStatus.SOURCE_MISSING}:
                    if not allow_missing:
                        raise SourceFileMissing(f)
                    continue
                if node.status in {NodeStatus.SOURCE_PRESENT, NodeStatus.SOURCE_PRESENT,
                                   NodeStatus.SCANNED_PRESENT_DEP}:
                    (self.sandbox / f).parent.mkdir(parents=True, exist_ok=True)
                    (self.sandbox / f).write_bytes((self.srcdir / f).read_bytes())
                    continue
                if node.status in {NodeStatus.BUILT_PRESENT, NodeStatus.BUILT_MISSING}:
                    continue
                raise Exception(f'implementation error {node.status.name}')
            for f in node.deps:
                (self.sandbox / f).write_bytes((self.srcdir / f).read_bytes())

    def _not_built(self):
        return [node for node in self.nodes
                if node.status in {NodeStatus.BUILT_MISSING, NodeStatus.NEEDS_REBUILT}]

    def _node_can_be_built(self, node: Node):
        if node.status not in {NodeStatus.BUILT_MISSING, NodeStatus.NEEDS_REBUILT}:
            return False
        for (_, source) in node.sources:
            node_source = self._find_node(source)
            if node_source.status in {NodeStatus.BUILT_MISSING, NodeStatus.SOURCE_MISSING,
                                      NodeStatus.NEEDS_REBUILT}:
                return False
            if node_source.status in {NodeStatus.BUILT_PRESENT, NodeStatus.SOURCE_PRESENT}:
                continue
            raise Exception(f'implementation error {node_source.status.name}')
        return True

    def _can_be_built(self) -> List[Node]:
        return [node for node in self.nodes if self._node_can_be_built(node)]

    def _move_node_artefacts(self, node):
        for (_, a) in node.artefacts:
            source: Path = self.sandbox / a
            if not source.exists():
                continue
            target: Path = source.with_suffix(source.suffix + '.copy')
            source.rename(target)

    def _check_rule_output(self, node):
        for (_, a) in node.artefacts:
            new_a: Path = self.sandbox / a
            # old_a: Path = new_a.with_suffix(new_a.suffix + '.copy')
            if not new_a.exists():
                raise TargetArtefactNotBuilt(a)

    def _build(self):
        self._scan()
        self._mount(allow_missing=False)

        while True:
            before = len(self._not_built())
            for node in self._can_be_built():
                if (node.ok_build is not None) and node.ok_build == node.deps_hash_hex():
                    continue
                self._move_node_artefacts(node)
                success = node.run()
                self._check_rule_output(node)
                node.ok_build = node.deps_hash_hex()
                print(f'{node.label}, success : {success}')
            after = len(self._not_built())
            if after == 0:
                self._stamp()
                return True
            if before == after:
                self._stamp()
                return False

    def _scan(self):
        self._mount(allow_missing=True)
        for node in self.nodes:
            if node.status != NodeStatus.SOURCE_PRESENT:
                continue
            (_, f) = node.artefacts[0]
            scanned_deps = node.scan(self.sandbox / f)
            for d in scanned_deps:
                if isinstance(d, str):
                    d = Path(d)
                if d.is_absolute():
                    d = d.relative_to(self.srcdir)
                if d not in node.deps:
                    node.deps.append(d)

    def _stamp(self):
        with open((self.sandbox) / 'lcpymake.json', 'w') as fin:
            json.dump(self._to_json(), fin)
