import networkx as nx
from pathlib import Path
from typing import List, Callable, Set, Tuple
import subprocess
import logging
logging.basicConfig(level=logging.INFO)

Rule = Tuple[str, Callable[[List[Path], List[Path]], subprocess.CompletedProcess]]


class TargetNotGeneratedException(Exception):
    def __init__(self, target: Path, process: subprocess.CompletedProcess):
        self.target = target
        self.process = process


class SourceNotFoundException(Exception):
    def __init__(self, source: Path):
        self.source = source


class Edge:
    def __init__(self, from_path: Path, to_path: Path, rule: Rule):
        self.from_path = from_path
        self.to_path = to_path
        self.rule = rule

    def __str__(self):
        return 'C'


class Command:
    def __init__(self, source: Path, target: Path):
        self.source = source
        self.target = target


class Graph:
    def __init__(self, basedir: Path):
        self.basedir = basedir
        self.graph = nx.DiGraph()

    def add_path(self, path: Path):
        self.graph.add_node(path.relative_to(self.basedir))

    def add_edge(self, fromp: Path, top: Path, rule: Rule):
        self.graph.add_edge(fromp.relative_to(self.basedir),
                            top.relative_to(self.basedir), rule=rule)

    def draw(self, file):
        order = list(nx.topological_sort(self.graph))
        order.reverse()
        logging.info(order)
        for node in order:
            logging.info(f'node : {node}')
            edges = self.graph.in_edges(node)
            for edge in edges:
                (from_p, to_p) = edge
                rule = self.graph.get_edge_data(from_p, to_p)['rule']
                logging.info(f'... edge : {edge}')
                logging.info(f'... rule : {rule}')

    def add_rule(self, rule: Rule, sources: List[Path], targets: List[Path]):
        for source in sources:
            self.add_path(source)
            for target in targets:
                self.add_path(target)
                self.add_edge(fromp=source, top=target, rule=rule([source], [target]))

    def build_target(self, rule: Rule, sources: List[Path], targets: List[Path]):
        for source in sources:
            logging.debug(f'test source {source}')
            if not source.exists():
                raise SourceNotFoundException(source)

        p = rule(sources, targets)

        if p.returncode != 0:
            raise Exception(f'rule return code : {p.returncode}, command was {p.args}')

        for target in targets:
            logging.debug(f'test target {target}')
            if not target.exists():
                raise TargetNotGeneratedException(target, p)


def subprocess_rule(rule):
    def f(a, b):
        return rule(a, b)
#    p = subprocess.run(['gcc', '-c', '-o', str(targets[0]), str(sources[0])])

    return f
