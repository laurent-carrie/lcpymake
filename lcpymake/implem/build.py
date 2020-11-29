import hashlib
import json
from pathlib import Path

from lcpymake.world import World
from lcpymake.node import Node
from lcpymake import logger


def node_is_candidate_for_build(w: World, node: Node):
    for in_node in node.in_nodes:
        if in_node.artefact_digest is None:
            return False
        if in_node.stored_digest != in_node.current_digest:
            return False

    if node.in_nodes == []:
        if node.current_digest == node.stored_digest:
            return False
        return True

    if node.artefact_digest is None:
        return True

    if node.current_digest == node.stored_digest:
        return False

    return True


def find_first_candidate_for_build(w: World):
    candidates = {
        node for node in w.nodes if node_is_candidate_for_build(w, node)
    }
    if candidates == set():
        logger.info("no candidate found for build")
        return None
    candidate: Node = sorted(candidates, key=lambda node: node.__repr__())[0]
    return candidate


def build_one_step(w: World):
    logger.info("build one step")

    candidate = find_first_candidate_for_build(w)
    logger.info(candidate)
    if candidate is None:
        return
    logger.info(candidate.is_source)

    if candidate.is_source:
        candidate.stored_digest = candidate.current_digest
        return

    sources = [w.sandbox / f for f in candidate.sources]
    artefacts = [w.sandbox / f for f in candidate.artefacts]
    try:
        logger.info(candidate.rule.info)
        success = candidate.rule.run(sources=sources, targets=artefacts)
        candidate.stored_digest = candidate.current_digest
        return success
    except Exception as e:
        logger.error(f"failed to run rule {candidate.rule.info}")
        raise RuntimeError(e) from e
