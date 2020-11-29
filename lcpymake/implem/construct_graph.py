import hashlib
import json
from pathlib import Path

from lcpymake.world import World
from lcpymake.node import Node
from lcpymake.implem.digest import calculate_hash_of_node, calculate_hash_of_deps_of_node
from lcpymake.implem.build import find_first_candidate_for_build
from lcpymake import logger


def find_node_for_artefact(w, artefact: str):
    assert(type(artefact) == str)
    candidates = [node for node in w.nodes if artefact in node.artefacts]
    if len(candidates) > 2:
        raise ValueError(f"artefact {artefact} found in more than one node")
    # if len(candidates) == 0:
    #    raise ValueError(f"artefact {artefact} not found")
    if len(candidates) == 1:
        return candidates[0]
    return None


def get_stored_hash(w: World, node: Node):
    if w.json_path().exists():
        with open(str(w.json_path()), 'r') as fin:
            j = json.load(fin)
            for node in w._source_nodes:
                d = j.get(node.__repr__())
                if d:
                    hash = d.get('stored_digest')
                    d.stored_digest = hash


def _mount_node(w: World, node: Node):
    if not node.is_source:
        logger.info(f"don't mount node {node} because it is source")
        return
    for f in node.artefacts:
        logger.info(f"mount {f}")
        if (w.srcdir / f).exists():
            (w.sandbox / f).parent.mkdir(parents=True, exist_ok=True)
            (w.sandbox / f).write_bytes((w.srcdir / f).read_bytes())
        else:
            logger.warning(f"cannot not mount non existing file : {w.srcdir/f}")


def reset_node(node):
    node.in_nodes = set()
    node.out_nodes = set()
    # node.stored_digest = None
    node.artefact_digest = None


def load_cached_digest(w: World):
    try:
        if w.json_path().exists():
            with open(str(w.json_path()), 'r') as fin:
                j = json.load(fin)
                for node in w.nodes:
                    try:
                        node.cached_digest = j[node.__repr__()]["cached_digest"]
                        node.stored_digest = node.cached_digest
                    except KeyError as e:
                        logger.error(f"key not found : {e}")
    except Exception as e:
        logger.error(e)


def construct_graph(w: World):
    for node in w.nodes:
        reset_node(node)

    # nodes that are not intermediary nodes
    w._root_nodes = set(w.nodes)
    w._source_nodes = set()

    for node in w.nodes:
        for file in node.sources:
            in_node = find_node_for_artefact(w, file)
            if in_node:
                node.in_nodes.add(in_node)
                in_node.out_nodes.add(node)
            else:
                raise ValueError(
                    f"for node {node.__repr__()}, cannot find node for source {file}")

    w._source_nodes = {node for node in w.nodes if node.in_nodes == set()}
    w._root_nodes = {node for node in w.nodes if node.out_nodes == set()}

    # mount first, scan is done in sandbox
    logger.info("SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS mount")
    for node in w._source_nodes:
        _mount_node(w, node)

    # run scanner
    for node in w.nodes:
        if not node.is_source:
            continue
        logger.info(f"scan {node} ; {node.scan}")
        if node.scan:
            for artefact in node.artefacts:
                for f in node.scan(w.sandbox / artefact):
                    logger.info(f"SSSSSSSSSSSSSSSSSSSSSSSSSSS {f}")
                    f = Path(f).relative_to(w.srcdir)
                    other_node = find_node_for_artefact(w, str(f))
                    if other_node is None:
                        logger.info(f"dep node not found, creating it : {f}")
                        other_node = Node(artefacts=[str(f)],
                                          sources=[], rule=None, scan=None)
                        reset_node(other_node)
                        w.nodes.append(other_node)
                        _mount_node(w, other_node)
                    logger.info(f"found dep : {other_node} ==> {node}")
                    node.in_nodes.add(other_node)
                    other_node.out_nodes.add(node)

    w._source_nodes = {node for node in w.nodes if node.in_nodes == set()}
    w._root_nodes = {node for node in w.nodes if node.out_nodes == set()}

    # update digest
    for node in w.nodes:
        node.artefact_digest = calculate_hash_of_node(w, node)
    for node in w.nodes:
        node.current_digest = calculate_hash_of_deps_of_node(node)

    w._first_candidate_for_build = find_first_candidate_for_build(w)
