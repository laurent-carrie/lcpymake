from typing import Optional
import hashlib
import json
from pathlib import Path

from lcpymake.world import World
from lcpymake.node import Node
from lcpymake import logger


def calculate_hash_of_node(node: Node):
    logger.info(f"compute digest of {node.label}")
    node_hash = hashlib.sha256()
    for s in node.artefacts:
        # logger.info(f"consider {s}")
        f: Path = node.sandbox / s
        if f.exists():
            node_hash.update(f.read_bytes())
        else:
            return None

    return node_hash.hexdigest()


def calculate_hash_of_deps_of_node(node: Node) -> Optional[str]:
    node_hash = hashlib.sha256()
    for in_node in node.in_nodes:
        if in_node.artefact_digest is None:
            node_hash = None
            return None
        node_hash.update(str.encode(in_node.artefact_digest))
    else:
        return None
    return node_hash.hexdigest()
