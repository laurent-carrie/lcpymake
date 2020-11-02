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
    PRESENT_IN_SOURCES = 1


class Node:
    def __init__(self, path: Path, is_source: bool):
        self.path = path
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

    def to_json(self):
        d = {}
        for node in self.graph.nodes:
            d[str(node.path)] = {
                'path': str(node.path)
            }
        return json.dumps(d)

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

        for component in nx.strongly_connected_components(self.graph):
            for node_key in component:
                node = self.graph.nodes[node_key]['node']
                if node.is_source:
                    if self.is_source_node_ok(node):
                        # text = colored(node, 'red', attrs=['reverse', 'blink'])
                        text = colored(node, 'green', attrs=[])
                    else:
                        text = colored(node, 'red', attrs=[])
                else:
                    text = colored(node, 'blue', attrs=[])
                    info = 'no rule'
                    if node.rule_info is not None:
                        info = node.rule_info
                    text = text + '\n... rule : ' + colored(info, 'blue', attrs=[])

                print(text)

                edges = self.graph.in_edges(node_key)
                for edge in edges:
                    (from_p, to_p) = edge
                    print(f'... source : {from_p}')

    def add_explicit_rule(self, sources: List[Path], targets: List[Path], rule: Rule):
        # self.graph.add_node(uuid.uuid1())
        rule_info = 'no rule'
        if rule is not None:
            rule_info = rule(sources, targets).info

        for s in sources:
            for t in targets:
                if self.graph.nodes.get(t) is None:
                    raise NoSuchNode(t)
                if self.graph.nodes.get(s) is None:
                    raise NoSuchNode(s)
                target_node: Node = self.graph.nodes[t]['node']
                if target_node.is_source:
                    raise CannotAddARuleForASourceNode(target_node)

                if target_node.rule_info is not None and target_node.rule_info != rule_info:
                    raise NodeAlreadyHasARule(target_node)
                target_node.rule_info = rule_info
                self.graph.add_edge(s, t)

                for component in nx.strongly_connected_components(self.graph):
                    if len(component) > 1:
                        self.graph.remove_edge(s, t)
                        raise CannotAddEdgeItWouldMakeALoop(s, t)

    def remove_node(self, path):
        self.graph.remove_node(path)

    def build(self):
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
