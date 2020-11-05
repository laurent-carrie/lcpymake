from typing import List
from pathlib import Path

from lcpymake.model import World
# pylint:disable=W0611
from lcpymake.model import ArtefactSeenSeveralTimes
from lcpymake.model import CannotAddARuleForASourceNode
from lcpymake.model import NodeAlreadyHasARule
from lcpymake.model import NoSuchNode
from lcpymake.model import TargetArtefactNotBuilt
from lcpymake.model import Rule
# pylint:enable=W0611

# pylint:disable=W0212


def create(srcdir: Path, sandbox: Path):
    return World(srcdir=srcdir, sandbox=sandbox)


def create_source_node(world: World, artefact: str, scan):
    if scan is None:
        def scan(_):
            return []
    if not callable(scan):
        raise ValueError('scan is not a callable')
    world._add_source_node(artefact=artefact, scan=scan)


def create_built_node(world: World, artefacts: List[str], sources: List[str], rule: Rule):
    world._add_built_node(artefacts=artefacts, sources=sources, rule=rule)


def to_json(world: World):
    return world._to_json()


def is_valid(world):
    return world._is_valid()


def gprint(world):
    world._print()


def scan_artefacts(world):
    world._scan()


def build(world):
    return world._build()
