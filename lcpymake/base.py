from enum import Enum
from termcolor import colored, cprint
import json
import networkx as nx
from pathlib import Path
from typing import List, Callable, Tuple
import subprocess
import logging
import uuid

logging.basicConfig(level=logging.INFO)


class Rule:
    def __init__(self, info: str, run):
        self.info = info
        self.run = run


class TargetNotGeneratedException(Exception):
    def __init__(self, target: Path, process: subprocess.CompletedProcess):
        self.target = target
        self.process = process


class SourceNotFoundException(Exception):
    def __init__(self, source: Path):
        self.source = source


class NodeAlreadyThere(Exception):
    def __init__(self, path: Path):
        self.path = path


class NodeAlreadyHasARule(Exception):
    def __init__(self, path: Path):
        self.path = path


class CannotAddEdgeItWouldMakeALoop(Exception):
    def __init__(self, path1: Path, path2: Path):
        self.path1 = path1
        self.path2 = path2


class CannotAddARuleForASourceNode(Exception):
    def __init__(self, path: Path):
        self.path = path


class NoSuchNode(Exception):
    def __init__(self, path: Path):
        self.path = path


class NodeStatus(Enum):
    SOURCE_PRESENT = 1
    SOURCE_MISSING = 2
    BUILT_PRESENT = 3
    BUILT_MISSING = 4


class Node:
    def __init__(self, path: Path, is_source: bool):
        self.path = str(path)
        self.is_source = is_source
        self.rule_info = None

    def __repr__(self):
        return f'{self.path}'

    def __hash__(self):
        return hash(self.path)

    def __eq__(self, other):
        return (
            self.__class__ == other.__class__
            and self.path == other.path
        )


class Edge:
    def __init__(self, from_path: Path, to_path: Path, rule):
        self.from_path = from_path
        self.to_path = to_path
        self.rule_info = None

    def __str__(self):
        return 'C'


class Command:
    def __init__(self, source: Path, target: Path):
        self.source = source
        self.target = target


class Graph:
    def __init__(self, sourcedir: Path, builddir: Path):
        self.sourcedir = sourcedir
        self.builddir = builddir
        self.graph = nx.DiGraph()

    def node_status(self, node: Node) -> NodeStatus:
        if node.is_source:
            if (self.sourcedir / node.path).exists():
                return NodeStatus.SOURCE_PRESENT
            else:
                return NodeStatus.SOURCE_MISSING
        else:
            if (self.builddir / node.path).exists():
                return NodeStatus.BUILT_PRESENT
            else:
                return NodeStatus.BUILT_MISSING

    def add_source_node(self, path: Path):
        node = Node(path=path, is_source=True)
        if str(path) in self.graph.nodes:
            raise NodeAlreadyThere(path)
        self.graph.add_node(str(path), node=node)

    def add_built_node(self, path: Path):
        node = Node(path, is_source=False)
        if str(path) in self.graph.nodes:
            raise NodeAlreadyThere(path)
        self.graph.add_node(str(path), node=node)

    def is_source_node_ok(self, node: Node):
        if not str(node.path) in self.graph.nodes:
            raise Exception('cannot call node in source, node {node}')
        if not node.is_source:
            raise Exception(
                'does not make sense to call this function on a non source node')
        return (self.sourcedir / node.path).exists()

    def print(self):
        # order = list(nx.topological_sort(self.graph))
        # order.reverse()
        # logging.info(order)

        seen_nodes_keys = []

        def look_for_candidate():
            for node_key in self.graph.nodes:
                assert (type(node_key) == str)
                if node_key in seen_nodes_keys:
                    continue
                edges = self.graph.out_edges(node_key)
                if len(edges) == 0:
                    return node_key
            return None

        def rec_print(indent, node_key):
            if node_key in seen_nodes_keys:
                return
            seen_nodes_keys.append(node_key)
            node = self.graph.nodes[node_key]['node']
            if self.node_status(node) == NodeStatus.SOURCE_PRESENT:
                # text = colored(node, 'red', attrs=['reverse', 'blink'])
                line1 = colored(node.path, 'green', attrs=[]) + ' (source)'
            elif self.node_status(node) == NodeStatus.SOURCE_MISSING:
                line1 = colored(node.path, 'red', attrs=['blink']) + ' (missing source)'
            elif self.node_status(node) == NodeStatus.BUILT_PRESENT:
                line1 = colored(node, 'blue', attrs=[]) + ' (built present)'
            elif self.node_status(node) == NodeStatus.BUILT_MISSING:
                line1 = colored(node, 'blue', attrs=['reverse']) + ' (built missing)'
            else:
                raise Exception('internal error')

            print(f"{'... ' * indent} > {line1}")
            if not node.is_source:
                print(f"{'... ' * (indent + 1)} {node.rule_info}")

            edges = self.graph.in_edges(node_key)
            for edge in edges:
                (from_p, to_p) = edge
                # print(f'... source : {from_p}')
                rec_print(indent + 1, from_p)

        while True:
            candidate = look_for_candidate()
            if candidate is None:
                break
            rec_print(0, candidate)

    def to_json(self):
        j = {}
        for node_key in self.graph.nodes:
            gnode = self.graph.nodes[node_key]
            node = gnode['node']
            j[node_key] = {'path': node.path, 'is_source': node.is_source,
                           'rule': node.rule_info, 'preds': [], 'status': self.node_status(node).name}
            edges = self.graph.in_edges(node_key)
            for (from_node, to_node) in edges:
                j[node_key]['preds'].append(from_node)

        return j

    def add_explicit_rule(self, sources: List[Path], targets: List[Path], rule):
        if rule is None:
            raise ValueError('cannot have a None rule')
        rule_info = rule(sources, targets).info

        for t in targets:
            gnode = self.graph.nodes.get(t, None)
            if gnode is None:
                raise NoSuchNode(t)
            target_node: Node = gnode['node']
            if target_node.rule_info is not None:
                raise NodeAlreadyHasARule(target_node)

        for s in sources:
            for t in targets:
                if self.graph.nodes.get(t) is None:
                    raise NoSuchNode(t)
                if self.graph.nodes.get(s) is None:
                    raise NoSuchNode(s)
                target_node: Node = self.graph.nodes[t]['node']
                if target_node.is_source:
                    raise CannotAddARuleForASourceNode(target_node)

                self.graph.add_edge(s, t, rule_info=rule_info)
                self.graph.edges[s, t].update({'rule': rule})

                for component in nx.strongly_connected_components(self.graph):
                    if len(component) > 1:
                        self.graph.remove_edge(s, t)
                        raise CannotAddEdgeItWouldMakeALoop(s, t)
                target_node.rule_info = rule_info

    def remove_node(self, path):
        self.graph.remove_node(path)

    def mount(self):
        for node_key in self.graph.nodes:
            node = self.graph.nodes[node_key]['node']
            if not node.is_source:
                continue

            source = self.sourcedir / node.path
            if not source.exists():
                raise SourceNotFoundException(source)
            target = self.builddir / node.path
            target.parent.mkdir(parents=True, exist_ok=True)
            print(f'copy {source} to {target}')
            target.write_bytes(source.read_bytes())

    def build(self):
        self.mount()
        self.builddir.mkdir(parents=True, exist_ok=True)

        def look_for_candidate():
            """
            a candidate for build is a node that is not built and whose none of its predecessors are not not_built
            """
            for node_key in self.graph.nodes:
                gnode = self.graph.nodes[node_key]
                node = gnode['node']
                if self.node_status(node) in {NodeStatus.SOURCE_MISSING, NodeStatus.SOURCE_PRESENT, NodeStatus.BUILT_PRESENT}:
                    continue
                edges = self.graph.in_edges(gnode)
                sources = [self.graph.nodes[key]['node'] for (key, _) in edges]
                sources_status = {self.node_status(source) for source in sources}
                if NodeStatus.SOURCE_MISSING in sources_status:
                    continue
                if NodeStatus.BUILT_MISSING in sources_status:
                    continue

                return node_key
            else:
                return None

        def one_build():
            before = self.to_json()
            candidate_key = look_for_candidate()
            if candidate_key is None:
                return
            # node = self.graph.nodes[candidate_key]['node']
            edges = self.graph.in_edges(candidate_key)
            sources = [self.graph.nodes[key]['node'] for (key, _) in edges]
            exist = {(self.builddir / source.path).exists() for source in sources}
            if exist == {True}:
                source_nodes: List[Node] = [self.graph.nodes[node_key]['node']
                                            for (node_key, _) in edges]
                target_nodes: List[Node] = [self.graph.nodes[node_key]['node']
                                            for (_, node_key) in edges]
                sources: List[Path] = [self.builddir / s.path for s in source_nodes]
                targets: List[Path] = list(
                    {self.builddir / t.path for t in target_nodes})

                for (a, b) in edges:
                    rule = self.graph.get_edge_data(a, b).get('rule', None)

                result_ok = rule(sources=sources, targets=targets).run()
                print(result_ok)

            after = self.to_json()
            if before == after:
                raise Exception('internal error, build did not progress')
            one_build()

        one_build()
