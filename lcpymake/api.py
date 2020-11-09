from typing import List
from pathlib import Path

from lcpymake.model import World
# pylint:disable=W0611
from lcpymake.base import NoSuchNode, Rule
from lcpymake.base import RuleFailed, TargetArtefactNotBuilt, NodeAlreadyHasARule, \
    CannotAddARuleForASourceNode, \
    ArtefactSeenSeveralTimes
# pylint:enable=W0611

from lcpymake.colored import color_map

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


def gprint(world, nocolor):
    world._print(nocolor)


def scan_artefacts(world):
    world._scan()


def add_automatic_rule(world, from_suffix: str, to_suffix: str, rule: Rule):
    world._add_automatic_rule(from_suffix=from_suffix, to_suffix=to_suffix, rule=rule)


def build(world):
    return world._build()


def update_color_map(_, d):
    color_map.update(d)
