import hashlib
import json
from pathlib import Path
from typing import List, Set, Callable
import collections
import traceback

from lcpymake.base import Node, NodeStatus, RuleFailed, TargetArtefactNotBuilt, SourceFileMissing, \
    ArtefactSeenSeveralTimes
from lcpymake.colored import colored_string
from lcpymake.base import NoSuchNode

from lcpymake import logger

# pylint:disable=E0401
# don't know why pylint complains about termcolor
# pylint:enable=E0401


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
        #        self._scan()
        #       self._mount(allow_missing=True)
        world_dict = [n.to_json() for n in self.nodes]
        world_dict_str = json.dumps(world_dict)
        j = json.loads(world_dict_str)
        return j

    def _add_source_node(self, artefact: str, scan: Callable[[str], List[str]]):
        new_node = Node(srcdir=self.srcdir, sandbox=self.sandbox,
                        artefacts=[('', artefact)], sources=[], rule=None, scan=scan, get_node=self._find_node)
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
                        artefacts=artefacts, sources=sources, rule=rule, scan=None,
                        get_node=self._find_node)
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

    def _print(self, nocolor):
        def print_tree(indent, node):
            # status = node.status
            text = f"{'...' * indent}{node.label}"
            print(f'{colored_string(choice=node.status.name, text=text,nocolor=nocolor)}')
            if not node.is_source:
                text = f"{'...' * (indent + 1)}{node.rule_info}"
                print(f"{colored_string(choice='RULE',text=text,nocolor=nocolor)}")
            else:
                for fdep in node.deps_in_srcdir:
                    text = f"{'...' * (indent + 1)}{fdep}"
                    print(f"{colored_string(choice='DEP', text=text,nocolor=nocolor)}")

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
                if node.status in {NodeStatus.SOURCE_PRESENT}:
                    (self.sandbox / f).parent.mkdir(parents=True, exist_ok=True)
                    (self.sandbox / f).write_bytes((self.srcdir / f).read_bytes())
                    continue
                if node.status in {NodeStatus.BUILD_UP_TO_DATE, NodeStatus.BUILT_MISSING}:
                    continue
                raise Exception(f'implementation error {node.status.name}')
            for f in node.deps_in_srcdir:
                if f.exists():
                    (self.sandbox / f).write_bytes((self.srcdir / f).read_bytes())

    def _not_built(self):
        return [node for node in self.nodes
                if node.status in {NodeStatus.BUILT_MISSING, NodeStatus.NEEDS_REBUILD}]

    def _node_can_be_built(self, node: Node):
        if node.status not in {NodeStatus.BUILT_MISSING, NodeStatus.NEEDS_REBUILD}:
            return False
        for (_, source) in node.sources:
            node_source = self._find_node(source)
            if node_source.status in {NodeStatus.BUILT_MISSING, NodeStatus.SOURCE_MISSING,
                                      NodeStatus.NEEDS_REBUILD}:
                return False
            if node_source.status in {NodeStatus.BUILD_UP_TO_DATE, NodeStatus.SOURCE_PRESENT}:
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
        logger.info("build")
        self._scan()
        self._mount(allow_missing=False)

        while True:
            logger.info("==== build iter")
            before = len(self._not_built())
            logger.info(f"before : {before}")
            for node in self._can_be_built():
                self._move_node_artefacts(node)
                try:
                    node.run()
                    self._check_rule_output(node)
                except Exception:
                    False
            after = len(self._not_built())
            if after == 0:
                self._stamp()
                return True
            if before == after:
                self._stamp()
                return False

    def _scan(self):
        logger.info("scan")
        self._mount(allow_missing=True)
        for node in self.nodes:
            node.stored_digest = None

            if node.status != NodeStatus.SOURCE_PRESENT:
                continue
            (_, f) = node.artefacts[0]
            scanned_deps = node.scan(self.sandbox / f)
            for d in scanned_deps:
                if isinstance(d, str):
                    d = Path(d)
                if d.is_absolute():
                    d = d.relative_to(self.srcdir)
                if d not in node.deps_in_srcdir:
                    node.deps_in_srcdir.append(d)

        if self.json_path().exists():
            try:
                with open(str(self.json_path()), 'r') as fin:
                    j = json.load(fin)
                    assert(type(j) == list)
                    for item in j:
                        node = self._find_node(item["artefacts"][0])
                        if node is None:
                            logger.warn(f"node not found {item['artefacts'][0]}")
                        elif not node.is_source and not node.is_scanned:
                            if not item.get("digest"):
                                logger.warn(f"no digest for node {node.label}")
                            else:
                                node.stored_digest = item["digest"]
            except Exception as e:
                logger.error(e)
                logger.error(traceback.format_exc())

    def json_path(self) -> Path:
        return self.sandbox / 'lcpymake.json'

    def _stamp(self):
        with open(str(self.json_path()), 'w') as fout:
            json.dump(self._to_json(), fout)
