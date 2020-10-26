from pathlib import Path
from typing import List, Callable
import subprocess
import logging
logging.basicConfig(level=logging.INFO)

Rule = Callable[[List[Path], List[Path]], subprocess.CompletedProcess]


class TargetNotGeneratedException(Exception):
    def __init__(self, target: Path, process: subprocess.CompletedProcess):
        self.target = target
        self.process = process


class SourceNotFoundException(Exception):
    def __init__(self, source: Path):
        self.source = source


def f(i, j):
    return i + j


def build_target(rule: Rule, sources: List[Path], targets: List[Path]):
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
