from typing import List
from pathlib import Path

from lcpymake.world import World
from lcpymake.node import Rule


def create(srcdir: Path, sandbox: Path):
    return World(srcdir=srcdir, sandbox=sandbox)


def create_source_node(world: World, artefact: str, scan):
    if scan is None:
        def scan(_):
            return []
    if not callable(scan):
        raise ValueError('scan is not a callable')
    world.add_source_node(artefact=artefact, scan=scan)


def create_built_node(world: World, artefacts: List[str], sources: List[str], rule: Rule):
    world.add_built_node(artefacts=artefacts, sources=sources, rule=rule)


def to_json(world: World):
    return world.to_json()


def gprint(world, nocolor):
    world._print(nocolor)


def scan_artefacts(world):
    world.scan()


def build(world):
    return world._build()


def mount(world):
    return world._mount(allow_missing=True)
