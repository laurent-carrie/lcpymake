from lcpymake.world import World


def find_node_for_artefact(w, artefact: str):
    candidates = [node for node in w.nodes if artefact in node.artefacts]
    if len(candidates) > 2:
        raise ValueError(f"artefact {artefact} found in more than one node")
    if len(candidates) == 1:
        return candidates[0]
    return None


def build_graph(w: World):
    for node in w.nodes:
        node.in_nodes = set()

    # nodes that are not intermediary nodes
    w.root_nodes = set(w.nodes)
    w.source_nodes = set()

    for node in w.nodes:
        if node.sources == []:
            w.source_nodes.add(node)
        for file in node.artefacts:
            in_node = find_node_for_artefact(w, file)
            if in_node:
                node.in_nodes.add(in_node)
                w.root_nodes.discard(in_node)
