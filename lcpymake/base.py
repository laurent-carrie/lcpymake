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
        self.is_source = None
        self.is_scanned = None
        self.deps_in_srcdir = []
        self.get_node = get_node

        self.stored_digest = None
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

    def deps_hash_hex_of_source_node(self):
        logger.info(f"compute digest of {self.label}")
        node_hash = hashlib.sha256()
        for (_, s) in self.artefacts:
            # logger.info(f"consider {s}")
            f: Path = self.sandbox / s
            if f.exists():
                node_hash.update(f.read_bytes())
            else:
                return None
        for s in self.deps_in_srcdir:
            # logger.info(f"consider {s}")
            f: Path = self.sandbox / s
            if f.exists():
                node_hash.update(f.read_bytes())
            else:
                return None

        return node_hash.hexdigest()

    def deps_hash_hex_of_built_node(self):
        logger.info(f"compute digest of {self.label}")
        if self.is_source or self.is_scanned:
            raise Exception('implementation error')
        node_hash = hashlib.sha256()
        node_hash.update(str.encode(self.rule_info))
        if True:
            for (_, s) in self.artefacts:
                f: Path = self.sandbox / s
                if f.exists():
                    node_hash.update(f.read_bytes())
                else:
                    return None
        for (_, s) in self.sources:
            node: Node = self.get_node(s)
            # logger.info(f"inspect {node.label}")
            for (_, s2) in node.artefacts:
                f: Path = self.sandbox / s2
                # logger.info(f"inspect artefact {f}")
                if f.exists():
                    node_hash.update(f.read_bytes())
                else:
                    return None
            for dep in node.deps_in_srcdir:
                f: Path = self.sandbox / dep
                # logger.info(f"inspect dep {f}")
                if f.exists():
                    node_hash.update(f.read_bytes())
                else:
                    return None

        return node_hash.hexdigest()

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
        except Exception as e:
            raise RuleFailed(self.rule_info, e) from e

    @property
    def label(self):
        not_qualified_artefacts = [str(s) for (_, s) in self.artefacts]
        return ';'.join(not_qualified_artefacts)

    def to_json(self):
        j = {'artefacts': [str(p) for (_, p) in self.artefacts]}
        j.update({'status': self.status.name})
        if not self.is_source and not self.is_scanned:
            j.update({'sources': [str(p) for (_, p) in self.sources]})
            j.update({'rule': self.rule_info})
        if self.is_source:
            j.update({'scanned_deps': [str(p) for p in self.deps_in_srcdir]})
        if not (self.is_source or self.is_scanned):
            j.update({'digest': self.deps_hash_hex()})

        return j

    @property
    def status(self):

        if self.is_scanned:
            assert False

        if self.is_source:
            if {(self.srcdir / s).exists() for (_, s) in self.artefacts} == {True}:
                return NodeStatus.SOURCE_PRESENT
            return NodeStatus.SOURCE_MISSING

        if {(self.sandbox / s).exists() for (_, s) in self.artefacts} == {True}:
            if self.stored_digest == self.deps_hash_hex():
                return NodeStatus.BUILD_UP_TO_DATE
        return NodeStatus.BUILT_MISSING


class NodeStatus(Enum):
    SOURCE_PRESENT = 1
    SOURCE_MISSING = auto()
    BUILD_UP_TO_DATE = auto()
    BUILT_MISSING = auto()
    NEEDS_REBUILD = auto()
    SCANNED_MISSING_DEP = auto()


class RuleFailed(Exception):
    def __init__(self, filename, msg):
        Exception.__init__(self, f'build failed for  : {filename} ; message is : {msg}')
        self.filename = filename
        self.msg = msg


class TargetArtefactNotBuilt(Exception):
    def __init__(self, filename):
        Exception.__init__(self, f'artefact was not built for : {filename}')
        self.filename = filename


class SourceFileMissing(Exception):
    def __init__(self, filename):
        Exception.__init__(self, f'source file missing : {filename}')
        self.filename = filename


class NodeAlreadyHasARule(Exception):
    def __init__(self):
        Exception.__init__(self)


class CannotAddARuleForASourceNode(Exception):
    def __init__(self):
        Exception.__init__(self)


class NoSuchNode(Exception):
    def __init__(self, filename):
        Exception.__init__(self, f'{filename}')


class ArtefactSeenSeveralTimes(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)


class Rule:
    def __init__(self, info: Callable[[List[str], List[str]], str],
                 run: Callable[[List[str], List[str]], bool]):
        self.info = info
        self.run = run
