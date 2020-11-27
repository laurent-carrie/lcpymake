import hashlib
import json
from pathlib import Path

from lcpymake.world import World
from lcpymake.node import Node
from lcpymake import logger


def find_node_for_artefact(w, artefact: str):
    candidates = [node for node in w.nodes if artefact in node.artefacts]
    if len(candidates) > 2:
        raise ValueError(f"artefact {artefact} found in more than one node")
    if len(candidates) == 0:
        raise ValueError(f"artefact {artefact} not found")
    if len(candidates) == 1:
        return candidates[0]
    return None


def calculate_hash_of_node(w: World, node: Node):
    logger.info(f"compute digest of {node.label}")
    node_hash = hashlib.sha256()
    for s in node.artefacts:
        # logger.info(f"consider {s}")
        f: Path = node.sandbox / s
        if f.exists():
            node_hash.update(f.read_bytes())
        else:
            return None
    # @todo : add deps

    return node_hash.hexdigest()


def get_stored_hash(w: World, node: Node):
    if w.json_path().exists():
        with open(str(w.json_path()), 'r') as fin:
            j = json.load(fin)
            for node in w._source_nodes:
                d = j.get(node.__repr__())
                if d:
                    hash = d.get('stored_digest')
                    d.stored_digest = hash


def _mount_sources(w: World):
    for node in w._source_nodes:
        for f in node.artefacts:
            if (w.srcdir / f).exists():
                (w.sandbox / f).parent.mkdir(parents=True, exist_ok=True)
                (w.sandbox / f).write_bytes((w.srcdir / f).read_bytes())


def build_graph(w: World):
    for node in w.nodes:
        node.in_nodes = set()
        node.out_nodes = set()
        node.stored_digest = None
        node.artefact_digest = None

    # nodes that are not intermediary nodes
    w._root_nodes = set(w.nodes)
    w._source_nodes = set()

    for node in w.nodes:
        for file in node.sources:
            in_node = find_node_for_artefact(w, file)
            if in_node:
                node.in_nodes.add(in_node)
                in_node.out_nodes.add(node)

    w._source_nodes = {node for node in w.nodes if node.in_nodes == set()}
    w._root_nodes = {node for node in w.nodes if node.out_nodes == set()}

    _mount_sources(w)

    # update digest
    for node in w.nodes:
        node.artefact_digest = calculate_hash_of_node(w, node)

    print("hello")
