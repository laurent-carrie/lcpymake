from lcpymake.world import World


def find_node_for_artefact(w, artefact: str):
    candidates = [node for node in w.nodes if artefact in node.artefacts]
    if len(candidates) > 2:
        raise ValueError(f"artefact {artefact} found in more than one node")
    if len(candidates) == 0:
        raise ValueError(f"artefact {artefact} not found")
    if len(candidates) == 1:
        return candidates[0]
    return None


def build_graph(w: World):
    for node in w.nodes:
        node.in_nodes = set()
        node.out_nodes = set()

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

    print("hello")
